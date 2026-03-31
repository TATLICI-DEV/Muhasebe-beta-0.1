"""
run.py  –  Muhasebe Beta EXE Girişi
Bu dosya PyInstaller tarafından paketlenir. Mevcut uygulama kodlarına
(main.py, pdf_parser.py, vb.) DOKUNULMAMISTIR.
"""
import sys
import os
import threading
import time
import webbrowser
import traceback
import ctypes

# ---------------------------------------------------------------
# PyInstaller frozen ortamı için çalışma dizinini ayarla
# ---------------------------------------------------------------
if getattr(sys, "frozen", False):
    # .exe olarak çalışıyoruz – dizin = .exe'nin bulunduğu yer
    BASE_DIR = os.path.dirname(sys.executable)
    # stdout/stderr'ı log dosyasına yönlendir
    LOG_FILE = os.path.join(BASE_DIR, "log.txt")
    sys.stdout = open(LOG_FILE, "a", encoding="utf-8")
    sys.stderr = sys.stdout
else:
    # Normal Python ile çalışıyoruz (test için)
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    LOG_FILE = os.path.join(BASE_DIR, "log.txt")

os.chdir(BASE_DIR)

# ---------------------------------------------------------------
# Hata loglama – uygulama kapanmasın, log.txt'e yaz
# ---------------------------------------------------------------
def log_error(msg: str):
    """Hata mesajını log.txt dosyasına yazar."""
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass  # log bile yazılamazsa sessizce devam et

def global_exception_handler(exc_type, exc_value, exc_tb):
    """Yakalanmamış tüm hataları loglar, uygulamayı kapatmaz."""
    err = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    log_error(f"YAKALANMAMIS HATA:\n{err}")
    if getattr(sys, "frozen", False):
        ctypes.windll.user32.MessageBoxW(0, "Uygulamada bir hata oluştu. Detaylar log.txt dosyasında.", "Hata", 0x10)

sys.excepthook = global_exception_handler

# ---------------------------------------------------------------
# Gerekli klasörler
# ---------------------------------------------------------------
for folder in ("uploads", "outputs", "static"):
    os.makedirs(os.path.join(BASE_DIR, folder), exist_ok=True)

# ---------------------------------------------------------------
# PyInstaller: _MEIPASS içindeki static/ dosyalarını exe dizinine kopyala
# (main.py göreceli 'static/index.html' yolunu kullanıyor)
# ---------------------------------------------------------------
if getattr(sys, "frozen", False):
    import shutil
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        src_static = os.path.join(meipass, "static")
        dst_static = os.path.join(BASE_DIR, "static")
        if os.path.isdir(src_static):
            for item in os.listdir(src_static):
                src_item = os.path.join(src_static, item)
                dst_item = os.path.join(dst_static, item)
                if not os.path.exists(dst_item):  # var olan dosyaların üzerine yazma
                    shutil.copy2(src_item, dst_item)

# ---------------------------------------------------------------
# Tarayıcıyı sunucu hazır olunca aç
# ---------------------------------------------------------------
HOST = "127.0.0.1"
PORT = 8000
URL  = f"http://{HOST}:{PORT}"

def open_browser():
    """Sunucu hazır olana kadar bekle, sonra tarayıcıyı aç."""
    import urllib.request
    for attempt in range(20):          # max 20 x 0.5s = 10 saniye bekle
        time.sleep(0.5)
        try:
            urllib.request.urlopen(f"http://{HOST}:{PORT}/", timeout=1)
            # Sunucu yanıt verdi — tarayıcıyı aç
            webbrowser.open(URL)
            return
        except Exception:
            continue
    # 10 saniye geçti, yine de dene
    try:
        webbrowser.open(URL)
    except Exception as e:
        log_error(f"Tarayıcı açılamadı: {e}")

threading.Thread(target=open_browser, daemon=True).start()

# ---------------------------------------------------------------
# FastAPI uygulamasını başlat
# ---------------------------------------------------------------
try:
    import uvicorn
    import main  # mevcut main.py – hiç değiştirilmedi
    uvicorn.run(main.app, host=HOST, port=PORT, log_level="warning", log_config=None)
except Exception as e:
    log_error(f"SUNUCU BASLATILAMADI:\n{traceback.format_exc()}")
    if getattr(sys, "frozen", False):
        ctypes.windll.user32.MessageBoxW(0, "Sunucu başlatılamadı. Detaylar log.txt dosyasında.", "Hata", 0x10)
    else:
        input(f"\n[HATA] Uygulama başlatılamadı. Detay için log.txt dosyasına bakın.\nÇıkmak için Enter'a basın...")
