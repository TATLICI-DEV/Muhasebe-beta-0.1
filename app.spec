# app.spec  -  PyInstaller build konfigurasyonu
# Kullanim: pyinstaller app.spec  veya  python build.py
# Cikti  : dist/app.exe

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

datas = []
datas += collect_data_files("pdfplumber")
datas += collect_data_files("pdfminer")
datas += collect_data_files("reportlab")
try:
    datas += collect_data_files("PIL")
except Exception:
    pass
datas += [("static", "static")]

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
    ["run.py"],
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
    name="app",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
