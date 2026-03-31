"""
run.py  -  Muhasebe Beta EXE Girisi
Bu dosya PyInstaller tarafindan paketlenir.
Mevcut kodlara (main.py, pdf_parser.py vb.) DOKUNULMAMISTIR.
"""
import sys
import os
import threading
import time
import webbrowser
import traceback
import ctypes

# ---------------------------------------------------------------
# PyInstaller frozen ortami icin calisma dizinini ayarla
# (main.py tum yollari goreceli kullaniyor - 'uploads/', 'static/' vb.)
# ---------------------------------------------------------------
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

LOG_FILE = os.path.join(BASE_DIR, "log.txt")

# --noconsole modunda stdout/stderr yoktur -> log dosyasina yonlendir
if getattr(sys, "frozen", False):
    _log_f = open(LOG_FILE, "a", encoding="utf-8", buffering=1)
    sys.stdout = _log_f
    sys.stderr = _log_f

# Calisma dizinini ata - TUM goreceli yollar buradan cozulecek
os.chdir(BASE_DIR)

# ---------------------------------------------------------------
# Gerekli klasorler (main.py bunlari kendisi olustursa da
# EXE ilk acilisinda garanti altin)
# ---------------------------------------------------------------
for _d in ("uploads", "outputs", "static"):
    os.makedirs(os.path.join(BASE_DIR, _d), exist_ok=True)

# ---------------------------------------------------------------
# PyInstaller: _MEIPASS icindeki static/ dosyalarini exe dizinine kopyala
# (main.py 'static/index.html' gibi goreceli yollar kullaniyor)
# ---------------------------------------------------------------
if getattr(sys, "frozen", False):
    import shutil as _shutil
    _meipass = getattr(sys, "_MEIPASS", None)
    if _meipass:
        _src = os.path.join(_meipass, "static")
        _dst = os.path.join(BASE_DIR, "static")
        if os.path.isdir(_src):
            for _item in os.listdir(_src):
                _s = os.path.join(_src, _item)
                _d2 = os.path.join(_dst, _item)
                if not os.path.exists(_d2):
                    _shutil.copy2(_s, _d2)

# ---------------------------------------------------------------
# Hata loglama
# ---------------------------------------------------------------
def log_error(msg: str):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
            f.flush()
    except Exception:
        pass

def _show_msgbox(text: str):
    try:
        ctypes.windll.user32.MessageBoxW(0, text, "Muhasebe Beta - Hata", 0x10)
    except Exception:
        pass

def global_exception_handler(exc_type, exc_value, exc_tb):
    err = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    log_error(f"YAKALANMAMIS HATA:\n{err}")
    if getattr(sys, "frozen", False):
        _show_msgbox(f"Beklenmedik hata:\n{exc_value}\n\nDetay: {LOG_FILE}")

sys.excepthook = global_exception_handler

# ---------------------------------------------------------------
# Tarayici - sunucu hazir olunca ac
# ---------------------------------------------------------------
HOST = "127.0.0.1"
PORT = 8000
URL  = f"http://{HOST}:{PORT}"

def open_browser():
    import urllib.request
    for _ in range(40):          # max 20 saniye bekle
        time.sleep(0.5)
        try:
            urllib.request.urlopen(f"http://{HOST}:{PORT}/", timeout=1)
            webbrowser.open(URL)
            return
        except Exception:
            continue
    # Yine de dene
    try:
        webbrowser.open(URL)
    except Exception as e:
        log_error(f"Tarayici acilamadi: {e}")

threading.Thread(target=open_browser, daemon=True).start()

# ---------------------------------------------------------------
# FastAPI'yi baslat
# KRITIK: uvicorn baslamadan hemen once cwd'yi tekrar ayarla
# (bazi kutuphaneler import sirasinda cwd degistirebilir)
# ---------------------------------------------------------------
try:
    os.chdir(BASE_DIR)   # guvenlik icin tekrar set et
    import uvicorn
    import main          # mevcut main.py - hic degistirilmedi
    uvicorn.run(main.app, host=HOST, port=PORT, log_config=None)
except Exception:
    log_error(f"SUNUCU BASLATILAMADI:\n{traceback.format_exc()}")
    if getattr(sys, "frozen", False):
        _show_msgbox(f"Sunucu baslatılamadı.\n\nDetay: {LOG_FILE}")
