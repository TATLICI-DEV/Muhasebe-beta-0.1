import pdfplumber
import re
import traceback
import sys
import json
import os

SETTINGS_FILE = "settings.json"

def get_heuristic_settings():
    if not os.path.exists(SETTINGS_FILE):
        return []
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def extract_text(pdf_path: str) -> str:
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
    except Exception as e:
        print(f"--- PDF OKUMA HATASI {pdf_path} ---")
        traceback.print_exc()
    return text

def safe_parse_money(m_str):
    if not m_str: return 0.0
    m_str = m_str.replace('.', '').replace(',', '.')
    try:
        return float(m_str)
    except:
        return 0.0

def parse_invoice(pdf_path: str) -> dict:
    """Temel stabil versiyon. Karmasik algoritmalar gecici olarak kaldirildi."""
    print(f"\n====================== PDF ISLENIYOR ======================")
    print(f"PATH: {pdf_path}")
    
    text = extract_text(pdf_path)
    
    # 2. Extract text log
    print("\n--- TEXT CIKTISI (ILK 300 KARAKTER) ---")
    print(text[:300] if text else "BOS METIN!")
    print("---------------------------------------\n")
    
    # 5. Guvenli fallback anahtar iskeleti
    data = {
        "invoice_date": {"value": "", "confidence": 0.0},
        "invoice_number": {"value": "", "confidence": 0.0},
        "vkn": {"value": "", "confidence": 0.0},
        "company_name": {"value": "", "confidence": 0.0},
        "vat_rate": {"value": 18, "confidence": 0.0},  # Varsayilan 18
        "base_amount": {"value": 0.0, "confidence": 0.0},
        "vat_amount": {"value": 0.0, "confidence": 0.0},
        "total_amount": {"value": 0.0, "confidence": 0.0},
        "expense_account": {"value": "770", "confidence": 1.0},
        "vat_account": {"value": "191", "confidence": 1.0},
        "vendor_account": {"value": "320", "confidence": 1.0},
        "raw_text": text 
    }
    
    if not text.strip():
        print("[HATA] PDF icerisinden metin cikarilamadi, bos format donduruluyor.")
        return data

    try:
        # ====================
        # FATURA TARIHI
        # ====================
        date_pattern_1 = r"\b\d{1,2}\s*[./-]\s*\d{1,2}\s*[./-]\s*\d{4}\b"
        date_pattern_2 = r"\b\d{1,2}\s+(?:Ocak|Şubat|Subat|Mart|Nisan|Mayıs|Mayis|Haziran|Temmuz|Ağustos|Agustos|Eylül|Eylul|Ekim|Kasım|Kasim|Aralık|Aralik)\s+\d{4}\b"
        
        date_matches = list(re.finditer(date_pattern_1, text))
        date_matches.extend(list(re.finditer(date_pattern_2, text, re.I)))
        if date_matches:
            if len(date_matches) == 1:
                val = date_matches[0].group(0)
                data["invoice_date"] = {"value": val, "confidence": 0.9}
                print(f"[BULUNDU] Fatura Tarihi (Regex): {val}")
            else:
                # Birden fazla varsa "Fatura Tarihi" veya "Tarih" gecen satira en yakin olani sec
                lines = text.split('\n')
                target_idx = -1
                for i, line in enumerate(lines):
                    if "tarih" in line.lower():
                        target_idx = i
                        break
                
                if target_idx != -1:
                    best_match = None
                    min_dist = 999
                    for match in date_matches:
                        val = match.group(0)
                        # Find line index of this value
                        val_idx = next((i for i, l in enumerate(lines) if val in l), -1)
                        if val_idx != -1:
                            dist = abs(val_idx - target_idx)
                            if dist < min_dist:
                                min_dist = dist
                                best_match = val
                    if best_match:
                        data["invoice_date"] = {"value": best_match, "confidence": 0.8}
                        print(f"[BULUNDU] Fatura Tarihi (Heuristic Yakinlik): {best_match}")
                    else:
                        data["invoice_date"] = {"value": date_matches[0].group(0), "confidence": 0.7}
                        print(f"[BULUNDU] Fatura Tarihi (Ilk Eslesme Fallback): {date_matches[0].group(0)}")
                else:
                    data["invoice_date"] = {"value": date_matches[0].group(0), "confidence": 0.7}
                    print(f"[BULUNDU] Fatura Tarihi (Ilk Eslesme): {date_matches[0].group(0)}")
        else:
            print("[BILGI] Fatura Tarihi bulunamadi.")

        # ====================
        # VKN / TCKN
        # ====================
        lines = text.split('\n')
        vkn_candidates = []
        for i, line in enumerate(lines):
            matches = re.findall(r"\b\d{10,11}\b", line)
            for m in matches:
                if not m.startswith("0"):
                    # Anahtar kelimenin kendi seyrinde oldugu gibi bir onceki satira da bakacagiz
                    prev_line = lines[i-1].upper() if i > 0 else ""
                    context = prev_line + " " + line.upper()
                    vkn_candidates.append({'val': m, 'context': context, 'line_idx': i, 'line': line})
                    
        if vkn_candidates:
            best_vkn = None
            # 1. Kural: Context icinde VKN ibaresi gecenleri bulalim
            val_scores = []
            for c in vkn_candidates:
                score = 0
                if any(k in c['context'] for k in ["VKN", "VERGI NO", "VERGİ NO", "TCKN", "VERGİ NUMARASI", "VERGI NUMARASI"]):
                    score += 100
                # Faturanin ust kisimlarindaysa ekstra puan (Satici genelde uste yazar)
                if c['line_idx'] < 15:
                    score += 50
                val_scores.append((c, score))
                
            val_scores.sort(key=lambda x: x[1], reverse=True)
            best_candidate, best_score = val_scores[0]
            
            if best_score > 0:
                best_vkn = best_candidate['val']
                data["vkn"] = {"value": best_vkn, "confidence": 0.9 if best_score >= 100 else 0.7}
                print(f"[BULUNDU] VKN/TCKN (Skor:{best_score}): {best_vkn}")
            else:
                best_vkn = vkn_candidates[0]['val']
                data["vkn"] = {"value": best_vkn, "confidence": 0.6}
                print(f"[BULUNDU] VKN/TCKN (Heuristic Ilk Deger): {best_vkn}")
        else:
            print("[BILGI] VKN/TCKN bulunamadi.")

        # ====================
        # FIRMA ADI (En Kritik)
        # ====================
        vkn_line_idx = -1
        if data["vkn"]["value"]:
            for c in vkn_candidates:
                if c['val'] == data["vkn"]["value"]:
                    vkn_line_idx = c['line_idx']
                    break
                    
        candidates = []
        # En ustu ekstra tarama alani yapalim, e-Arsivlerde satici en usttedir
        start_idx = 0
        end_idx = min(len(lines), vkn_line_idx + 5) if vkn_line_idx != -1 else min(len(lines), 10)
        
        for i in range(start_idx, end_idx):
            line = lines[i].strip()
            # Kisa veya anahtar kelime iceren bos satirlari gec
            if len(line) > 5 and not any(k in line.upper() for k in ["VKN", "VERGI", "TARIH", "FATURA", "TOPLAM", "NO:", "MERSIS", "SICIL", "SAYIN", "SAYIN:"]):
                candidates.append((line, i))
                
        if candidates:
            def score_company(item):
                c, idx = item
                cu = c.upper()
                score = len(c)
                if cu == c and any(char.isalpha() for char in c): 
                    score += 50
                # Harf bozulmalari vs icin ekstra turkce ibareler
                for kw in ["LTD", "A.Ş", "A.S.", "ŞTİ", "STI", "SANAYİ", "SANAYI", "TİCARET", "TICARET", "GIDA", "PAZARLAMA", "HIZMETLERI", "HİZMETLERİ", "A."]:
                    if kw in cu: score += 100
                    
                # Ust satirda olanlara oncelik ver. idx=0 -> +50, idx=5 -> +25
                loc_bonus = max(0, 50 - (idx * 5))
                score += loc_bonus
                
                return score
                
            candidates.sort(key=score_company, reverse=True)
            data["company_name"] = {"value": candidates[0][0], "confidence": 0.8}
            print(f"[BULUNDU] Firma Adi (Heuristic Score): {candidates[0][0]}")
        else:
            print("[BILGI] Firma Adi bulunamadi.")

        # ====================
        # FATURA NUMARASI
        # ====================

        inv_match = re.search(r'([A-Za-z0-9]{3}20\d{11})', text) # e-Fatura formati (16 hane AAA20YYYY9999999)
        if not inv_match:
            inv_match = re.search(r'(?:Fatura|Belge)\s*(?:No|Numaras[ıi])?[\:\s]*([A-Za-z0-9\-\/]{4,})', text, re.I)
        if not inv_match:
            inv_match = re.search(r'([A-Z]{2,3}\-?\d{6,14})', text) # Diger tip faturalar
            
        if inv_match:
            val = inv_match.group(1).strip()
            data["invoice_number"] = {"value": val, "confidence": 0.9}
            print(f"[BULUNDU] Fatura No (Regex): {val}")
        else:
            print("[BILGI] Fatura No Regex ile bulunamadi, Sezgisel (Heuristic) arama basliyor...")
            # Heuristic Logic
            keywords = ["Fatura", "Invoice", "Belge", "Evrak", "No", "Numara", "Seri No"]
            lines = text.split('\n')
            candidates = []
            
            for i, line in enumerate(lines):
                if any(kw.lower() in line.lower() for kw in keywords):
                    # Kendi satiri ve eger numarayi bir alt satira yazmissa diye +1 alt satiri tarayalim
                    lines_to_check = [line]
                    if i + 1 < len(lines):
                        lines_to_check.append(lines[i+1])
                    
                    for l_check in lines_to_check:
                        words = l_check.split()
                        for word in words:
                            # Sadece rakam ve harf birak
                            clean_word = re.sub(r'[^A-Za-z0-9]', '', word)
                            if len(clean_word) >= 4 and not any(kw.lower() in clean_word.lower() for kw in ["fatura", "invoice", "belge", "evrak", "tarih"]):
                                candidates.append(clean_word)
            
            print(f"[BILGI] Fatura No Heuristic aday(lar)i: {list(set(candidates))}")
            
            if candidates:
                # Ozel puanlama sistemi
                def score_candidate(c):
                    score = len(c)
                    has_alpha = any(ch.isalpha() for ch in c)
                    has_digit = any(ch.isdigit() for ch in c)
                    if has_alpha and has_digit:
                        score += 50
                    if len(c) == 16: # Tam bir e-Fatura/e-Arsiv numarasi formatindaysa
                        score += 200
                    return score
                
                candidates.sort(key=score_candidate, reverse=True)
                best_match = candidates[0]
                
                data["invoice_number"] = {"value": best_match, "confidence": 0.7}
                print(f"[BULUNDU] Fatura No (Heuristic): {best_match}")
            else:
                data["invoice_number"] = {"value": None, "confidence": 0.0}
                print("[BULUNAMADI] Fatura No (Regex ve Heuristic basarisiz)")

        money_pattern = r'(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2}))'
        
        # Matrah
        base_match = re.search(r'(?:Matrah|Mal\s*Hizmet\s*Top|Ara\s*Toplam)[\:\s]*' + money_pattern, text, re.I)
        if base_match:
            val = safe_parse_money(base_match.group(1))
            data["base_amount"] = {"value": val, "confidence": 0.9}
            print("[BULUNDU] Matrah (Regex):", val)
        else:
            print("[BILGI] Matrah mevcut regex (Matrah, Ara Toplam vs.) ile bulunamadi.")

        # KDV Tutarı
        vat_match = re.search(r'(?:Hesaplanan\s*KDV|KDV\s*Tutar(?:i)?|Vergi)[\:\s]*' + money_pattern, text, re.I)
        if vat_match:
            val = safe_parse_money(vat_match.group(1))
            data["vat_amount"] = {"value": val, "confidence": 0.9}
            print("[BULUNDU] KDV Tutari (Regex):", val)
        else:
            print("[BILGI] KDV Tutari mevcut regex (KDV Tutari, Vergi) ile bulunamadi.")

        # Toplam
        tot_match = re.search(r'(?:Genel\s*Toplam|Ödenecek\s*Tutar|Top\.|Tutar|Toplam)[\:\s]*' + money_pattern, text, re.I)
        if tot_match:
            val = safe_parse_money(tot_match.group(1))
            data["total_amount"] = {"value": val, "confidence": 0.9}
            print("[BULUNDU] Genel Toplam (Regex):", val)
        else:
            print("[BILGI] Genel Toplam mevcut regex ile bulunamadi.")


        # ---------------------------------------------
        # KDV ORANI TESPITI VE EKSIK VERI TAMAMLAMA
        # ---------------------------------------------
        rates_found = set(re.findall(r'%(\d{1,2})\b', text))
        valid_rates = [1, 10, 20]  # Oneri: 1, 10, 20
        matched_rates = [int(r) for r in rates_found if int(r) in valid_rates]
        
        base_val = data["base_amount"]["value"]
        vat_val = data["vat_amount"]["value"]
        tot_val = data["total_amount"]["value"]
        
        final_rate = 0
        conf_rate = 0.0
        
        # 1. Matrah ve KDV varsa saglama-hesaplama yap
        if base_val > 0 and vat_val > 0:
            calc_rate = round((vat_val / base_val) * 100)
            if calc_rate in valid_rates:
                final_rate = calc_rate
                conf_rate = 0.8
                print(f"[HESAPLANDI] KDV Orani ({calc_rate}%) matrah ve KDV uzerinden hesaplandi.")
                if calc_rate in matched_rates:
                    conf_rate = 0.9
                    print("[BILGI] KDV Orani hesaplamasi metindeki % degeriyle eslesti.")
        
        # 2. Metinde orani yakaladik mi
        if final_rate == 0 and matched_rates:
            final_rate = max(matched_rates)
            conf_rate = 0.7
            print(f"[BULUNDU] KDV Orani ({final_rate}%) metinden sezgisel bulundu.")
            
        # 3. Fallback
        if final_rate == 0:
            final_rate = 20
            conf_rate = 0.3
            print("[BILGI] KDV Orani bulunamadi. Varsayilan %20 atandi (estimated).")
            
        data["vat_rate"] = {"value": final_rate, "confidence": conf_rate}

        # ---------------------------------------------
        # EKSİK TUTAR HESAPLAMALARI
        # ---------------------------------------------
        r = final_rate / 100.0
        
        # Senaryo 1: Sadece Toplam var
        if tot_val > 0 and base_val == 0 and vat_val == 0:
            base_val = round(tot_val / (1 + r), 2)
            vat_val = round(tot_val - base_val, 2)
            data["base_amount"] = {"value": base_val, "confidence": 0.5}
            data["vat_amount"] = {"value": vat_val, "confidence": 0.5}
            print(f"[HESAPLANDI] Matrah ({base_val}) ve KDV ({vat_val}) Toplam uzerinden matematiksel olarak bulundu.")

        # Senaryo 2: Sadece Matrah var
        elif base_val > 0 and tot_val == 0 and vat_val == 0:
            vat_val = round(base_val * r, 2)
            tot_val = round(base_val + vat_val, 2)
            data["vat_amount"] = {"value": vat_val, "confidence": 0.5}
            data["total_amount"] = {"value": tot_val, "confidence": 0.5}
            print(f"[HESAPLANDI] KDV ({vat_val}) ve Toplam ({tot_val}) Matrah uzerinden matematiksel olarak bulundu.")

        # Senaryo 3: Matrah ve KDV var ama toplam yok
        elif base_val > 0 and vat_val > 0 and tot_val == 0:
            tot_val = round(base_val + vat_val, 2)
            data["total_amount"] = {"value": tot_val, "confidence": 0.5}
            print(f"[HESAPLANDI] Toplam ({tot_val}) Matrah ve KDV uzerinden matematiksel olarak bulundu.")
            
        # ---------------------------------------------
        # AKILLI HESAP KODU ATAMASI (HEURISTIC NLP)
        # ---------------------------------------------
        
        comp_name = data["company_name"]["value"]
        if comp_name:
            comp_name_u = comp_name.upper()
            settings = get_heuristic_settings()
            
            best_rule = None
            best_match_len = 0
            
            for rule in settings:
                keywords = [k.strip().upper() for k in rule.get("keywords", "").split(",") if k.strip()]
                for kw in keywords:
                    if kw in comp_name_u:
                        if len(kw) > best_match_len:
                            best_match_len = len(kw)
                            best_rule = rule
                            
            if best_rule:
                acc_code = best_rule.get("code", "770")
                data["expense_account"] = {"value": acc_code, "confidence": 0.9}
                print(f"[AKILLI ATAMA - DINAMIK] Gider Hesabi -> {acc_code} (Match: {best_match_len} chars)")
            else:
                data["expense_account"] = {"value": "770", "confidence": 0.5}
                print(f"[AKILLI ATAMA] Varsayilan Gider Hesabi -> 770 (Eslesme Yok)")
            
    except Exception as e:
        print("!!! BEKLENMEYEN HATA OLUSTU !!!")
        traceback.print_exc()
        
    print("===========================================================\n")
    return data

if __name__ == "__main__":
    from reportlab.pdfgen import canvas
    import os
    
    test_pdf_1 = "debug_fatura_1.pdf"
    test_pdf_2 = "debug_fatura_2.pdf"
    
    # PDF 1: Regex 
    c = canvas.Canvas(test_pdf_1)
    c.drawString(100, 700, "FATURA BILGILERI")
    c.drawString(100, 680, "Fatura Tarihi: 15.05.2023")
    c.drawString(100, 660, "Vergi No: 1234567890")
    c.drawString(100, 640, "ORNEK YAZILIM LTD STI")
    c.drawString(100, 620, "Fatura No: GIB2023000000001")
    c.drawString(100, 600, "Matrah: 1.000,00")
    c.drawString(100, 580, "Hesaplanan KDV: 200,00")
    c.drawString(100, 560, "Genel Toplam: 1.200,00")
    c.save()

    # PDF 2: Heuristic 
    c2 = canvas.Canvas(test_pdf_2)
    c2.drawString(100, 700, "Evrak Sira Numarasi ABC9876543X")
    c2.drawString(100, 680, "DANDIK MUSTERI A.S.")
    c2.drawString(100, 660, "Burada %20 yaziyordu bir yerlerde")
    c2.drawString(100, 640, "Tutar:  120.00")
    c2.drawString(100, 620, "10-10-2024 / 05321234567 / 9999999999")
    c2.save()
    
    print("\n--- TEST BASLIYOR ---\n")
    print(">>> 1. TEST (Regex Bekleniyor) <<<")
    sonuc1 = parse_invoice(test_pdf_1)
    print("\n[TEST 1] Dondurulen SOZLUK (JSON):\n", sonuc1)

    print("\n===========================================================")
    print(">>> 2. TEST (Heuristic Bekleniyor) <<<")
    sonuc2 = parse_invoice(test_pdf_2)
    print("\n[TEST 2] Dondurulen SOZLUK (JSON):\n", sonuc2)
    
    if os.path.exists(test_pdf_1):
        os.remove(test_pdf_1)
    if os.path.exists(test_pdf_2):
        os.remove(test_pdf_2)
