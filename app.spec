# app.spec  –  PyInstaller build konfigürasyonu
# Kullanım: pyinstaller app.spec
# Çıktı  : dist/app.exe

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# pdfplumber ve pdfminer veri dosyaları
datas = []
datas += collect_data_files("pdfplumber")
datas += collect_data_files("pdfminer")
datas += collect_data_files("reportlab")

# Pillow veri dosyaları
try:
    datas += collect_data_files("PIL")
except Exception:
    pass

# Static klasörü exe ile birlikte paketle
datas += [("static", "static")]

# Gizli importlar (uvicorn / fastapi iç modülleri çoğu zaman otomatik tespit edilemez)
hiddenimports = []
hiddenimports += collect_submodules("uvicorn")
hiddenimports += collect_submodules("fastapi")
hiddenimports += collect_submodules("sqlalchemy")
hiddenimports += collect_submodules("pdfplumber")
hiddenimports += collect_submodules("pdfminer")
hiddenimports += collect_submodules("reportlab")
hiddenimports += collect_submodules("PIL")
hiddenimports += [
    "anyio",
    "anyio._backends._asyncio",
    "anyio._backends._trio",
    "starlette",
    "starlette.routing",
    "starlette.staticfiles",
    "starlette.responses",
    "multipart",
    "email.mime.text",
    "email.mime.multipart",
    "reportlab",
    "reportlab.lib",
    "reportlab.lib.colors",
    "reportlab.lib.styles",
    "reportlab.lib.units",
    "reportlab.lib.pagesizes",
    "reportlab.lib.rl_accel",
    "reportlab.lib.utils",
    "reportlab.platypus",
    "reportlab.pdfgen",
    "reportlab.pdfgen.canvas",
    "PIL",
    "PIL.Image",
    "PIL.ImageDraw",
    "openpyxl",
]

a = Analysis(
    ["run.py"],          # Giriş noktası (DEĞİŞTİRİLMEDİ – main.py'ye dokunulmadı)
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "matplotlib",
        "cv2",
        "torch",
        "tensorflow",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="app",            # dist/app.exe
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,         # Konsol penceresi açılmasın (arka planda çalışsın)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,             # İkon eklemek isterseniz: icon="logo.ico"
)
