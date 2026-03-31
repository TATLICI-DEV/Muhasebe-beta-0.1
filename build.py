"""
build.py  -  Tek komutla exe uret
Kullanim : py -3 build.py
Cikti    : dist/app.exe
"""
import subprocess
import sys
import os
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))

def run(cmd, **kwargs):
    print(f"\n>>> {' '.join(str(c) for c in cmd)}\n")
    result = subprocess.run(cmd, **kwargs)
    if result.returncode != 0:
        print(f"\n[HATA] Komut basarisiz oldu (kod {result.returncode}).")
        sys.exit(result.returncode)

def check_pyinstaller():
    try:
        import PyInstaller  # noqa
    except ImportError:
        print("[BILGI] PyInstaller bulunamadi, yukleniyor...")
        run([sys.executable, "-m", "pip", "install", "pyinstaller"])

def check_dependencies():
    req = os.path.join(ROOT, "requirements.txt")
    if os.path.exists(req):
        print("[BILGI] Bagimliliklar kontrol ediliyor...")
        run([sys.executable, "-m", "pip", "install", "-r", req, "--quiet"])

def clean_build():
    for folder in ("build", "dist"):
        path = os.path.join(ROOT, folder)
        if os.path.exists(path):
            print(f"[BILGI] '{folder}/' siliniyor...")
            shutil.rmtree(path)

def build_exe():
    spec = os.path.join(ROOT, "app.spec")
    run([sys.executable, "-m", "PyInstaller", "--clean", spec], cwd=ROOT)

def verify_output():
    exe_path = os.path.join(ROOT, "dist", "app.exe")
    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print(f"\n{'='*55}")
        print(f"  BASARILI! -> {exe_path}")
        print(f"  Boyut: {size_mb:.1f} MB")
        print(f"{'='*55}\n")
    else:
        print("\n[HATA] dist/app.exe bulunamadi.")
        sys.exit(1)

if __name__ == "__main__":
    print("=" * 55)
    print("  Muhasebe Beta - EXE Build")
    print("=" * 55)
    check_pyinstaller()
    check_dependencies()
    clean_build()
    build_exe()
    verify_output()
