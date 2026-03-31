import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def generate_invoice_pdf(data: dict, output_path: str):
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "Fatura ve Muhasebe Kaydi Ozeti")
    
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 100, f"Fatura No: {data.get('invoice_number', '')}")
    c.drawString(50, height - 120, f"Fatura Tarihi: {data.get('invoice_date', '')}")
    # UTF karakter sorununu asmak icin ingilizce karakter basiyoruz, gercek provalarda font destegi eklenir.
    company_name = data.get('company_name', '').encode('ascii', 'ignore').decode('ascii')
    c.drawString(50, height - 140, f"Firma Adi: {company_name}")
    c.drawString(50, height - 160, f"VKN/TCKN: {data.get('vkn', '')}")
    
    def get_float(key):
        val = data.get(key, 0)
        try: return float(val) if val else 0.0
        except: return 0.0

    c.drawString(50, height - 200, f"Matrah: {get_float('base_amount'):.2f} TL")
    c.drawString(50, height - 220, f"KDV Orani: %{data.get('vat_rate', 0)}")
    c.drawString(50, height - 240, f"KDV Tutari: {get_float('vat_amount'):.2f} TL")
    c.drawString(50, height - 260, f"Genel Toplam: {get_float('total_amount'):.2f} TL")
    
    c.line(50, height - 280, width - 50, height - 280)
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 310, "Otomatik Muhasebe Kaydi (Yevmiye Fisi)")
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 340, "Hesap Kodu")
    c.drawString(200, height - 340, "Hesap Adi")
    c.drawString(400, height - 340, "Borc")
    c.drawString(480, height - 340, "Alacak")
    
    c.line(50, height - 345, width - 50, height - 345)
    
    c.setFont("Helvetica", 12)
    y_pos = height - 365
    
    # Gider
    c.drawString(50, y_pos, str(data.get('expense_account', '770')))
    c.drawString(200, y_pos, "Genel Giderler")
    c.drawString(400, y_pos, f"{get_float('base_amount'):.2f}")
    c.drawString(480, y_pos, "")
    y_pos -= 20
    
    # 191
    c.drawString(50, y_pos, str(data.get('vat_account', '191')))
    c.drawString(200, y_pos, "Indirilecek KDV")
    c.drawString(400, y_pos, f"{get_float('vat_amount'):.2f}")
    c.drawString(480, y_pos, "")
    y_pos -= 20
    
    # 320
    c.drawString(50, y_pos, str(data.get('vendor_account', '320')))
    c.drawString(200, y_pos, "Saticilar")
    c.drawString(400, y_pos, "")
    c.drawString(480, y_pos, f"{get_float('total_amount'):.2f}")
    
    c.save()
    return output_path
