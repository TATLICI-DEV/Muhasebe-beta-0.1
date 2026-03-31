from fastapi import FastAPI, UploadFile, File, Form, Depends, Request
from typing import List
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import shutil
import os
import json

import models
from database import engine, SessionLocal
from pdf_parser import parse_invoice
from report_generator import generate_batch_excel, generate_batch_pdf
from pydantic import BaseModel
from typing import List

class BatchRequest(BaseModel):
    invoice_ids: List[int]

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

os.makedirs("static", exist_ok=True)
os.makedirs("uploads", exist_ok=True)
os.makedirs("outputs", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def read_index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.post("/api/upload")
async def upload_pdf(files: List[UploadFile] = File(...)):
    processed_list = []
    for file in files:
        file_path = os.path.join("uploads", file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        extracted_data = parse_invoice(file_path)
        extracted_data["filename"] = file.filename
        processed_list.append(extracted_data)
        
    return {"status": "success", "data": processed_list}

@app.post("/api/save")
async def save_invoice(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    
    db_invoice = models.Invoice(
        invoice_date=data.get("invoice_date"),
        invoice_number=data.get("invoice_number"),
        vkn=data.get("vkn"),
        company_name=data.get("company_name"),
        vat_rate=float(data.get("vat_rate", 0) or 0),
        base_amount=float(data.get("base_amount", 0)  or 0),
        vat_amount=float(data.get("vat_amount", 0)  or 0),
        total_amount=float(data.get("total_amount", 0)  or 0),
        expense_account=data.get("expense_account", "770"),
        vat_account=data.get("vat_account", "191"),
        vendor_account=data.get("vendor_account", "320")
    )
    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)
    
    return {"status": "success", "message": "Muhasebeleştirildi", "invoice_id": db_invoice.id}

@app.post("/api/generate_batch")
async def generate_batch_report(request: BatchRequest, db: Session = Depends(get_db)):
    invoices = db.query(models.Invoice).filter(models.Invoice.id.in_(request.invoice_ids)).all()
    if not invoices:
        return {"status": "error", "message": "Fatura bulunamadi"}
        
    date_str = str(invoices[0].id)
    pdf_filename = f"Toplu_Yevmiye_Fisi_Batch_{date_str}.pdf"
    pdf_path = os.path.join("outputs", pdf_filename)
    generate_batch_pdf(invoices, pdf_path)
    
    excel_filename = f"Toplu_Yevmiye_Fisi_Batch_{date_str}.xlsx"
    excel_path = os.path.join("outputs", excel_filename)
    generate_batch_excel(invoices, excel_path)
    
    return {
        "status": "success", 
        "pdf_url": f"/api/download/{pdf_filename}",
        "excel_url": f"/api/download/{excel_filename}"
    }

@app.get("/api/invoices")
async def get_all_invoices(db: Session = Depends(get_db)):
    invoices = db.query(models.Invoice).order_by(models.Invoice.id.desc()).all()
    return {"status": "success", "data": invoices}

@app.delete("/api/invoices")
async def delete_invoices(request: BatchRequest, db: Session = Depends(get_db)):
    db.query(models.Invoice).filter(models.Invoice.id.in_(request.invoice_ids)).delete(synchronize_session=False)
    db.commit()
    return {"status": "success", "message": f"{len(request.invoice_ids)} adet islem silindi."}

# Settings API
SETTINGS_FILE = "settings.json"

@app.get("/api/settings")
async def read_settings():
    if not os.path.exists(SETTINGS_FILE):
        return {"status": "success", "data": []}
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = []
    return {"status": "success", "data": data}

@app.post("/api/settings")
async def update_settings(request: Request):
    new_settings = await request.json()
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(new_settings, f, indent=4, ensure_ascii=False)
    return {"status": "success", "message": "Ayarlar kaydedildi."}

@app.get("/api/download/{filename}")
async def download_file(filename: str):
    file_path = os.path.join("outputs", filename)
    if filename.endswith(".xlsx"):
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        media_type = "application/pdf"
    return FileResponse(path=file_path, filename=filename, media_type=media_type)
