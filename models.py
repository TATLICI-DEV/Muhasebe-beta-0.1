from sqlalchemy import Column, Integer, String, Float, DateTime
from database import Base
import datetime

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    invoice_date = Column(String, index=True)
    invoice_number = Column(String, index=True) # Aynı fatura numarası farklı sistemlerden gelebilir diye unique yapmıyoruz şimdilik (veya ekleriz)
    vkn = Column(String, index=True)
    company_name = Column(String)
    
    vat_rate = Column(Float)
    base_amount = Column(Float)
    vat_amount = Column(Float)
    total_amount = Column(Float)
    
    # Muhasebe Kayıtları
    expense_account = Column(String, default="770")  # Gider hesabı (Genel Gider)
    vat_account = Column(String, default="191")      # İndirilecek KDV
    vendor_account = Column(String, default="320")   # Satıcılar
