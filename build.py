"""
build.py  –  Tek komutla exe üret
Kullanım : python build.py
Çıktı    : dist/app.exe

Mevcut kaynak kodlara DOKUNULMAZ.
Sadece PyInstaller ile paketleme yapar.
"""

import subprocess
import sys
import os
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))

def run(cmd, **kwargs):
    print(f"\n>>> {' '.join(cmd)}\n")
    result = subprocess.run(cmd, **kwargs)
    if result.returncode != 0:
        print(f"\n[HATA] Komut başarısız oldu (kod {result.returncode}). Yukarıdaki çıktıyı inceleyin.")
        sys.exit(result.returncode)

def check_pyinstaller():
    """PyInstaller yüklü değilse yükle."""
    try:
        import PyInstaller  # noqa
    except ImportError:
        print("[BİLGİ] PyInstaller bulunamadı, yükleniyor...")
        run([sys.executable, "-m", "pip", "install", "pyinstaller"])

def check_dependencies():
    """requirements.txt'teki bağımlılıkların yüklü olduğundan emin ol."""
    req = os.path.join(ROOT, "requirements.txt")
    if os.path.exists(req):
        print("[BİLGİ] Bağımlılıklar kontrol ediliyor / yükleniyor...")
        run([sys.executable, "-m", "pip", "install", "-r", req, "--quiet"])
    else:
        print("[UYARI] requirements.txt bulunamadı, atlanıyor.")

def clean_build():
    """Eski build/dist klasörlerini temizle."""
    for folder in ("build", "dist"):
        path = os.path.join(ROOT, folder)
        if os.path.exists(path):
            print(f"[BİLGİ] Eski '{folder}/' klasörü siliniyor...")
            shutil.rmtree(path)

def build_exe():
    """PyInstaller ile exe oluştur."""
    spec = os.path.join(ROOT, "app.spec")
    run(
        [sys.executable, "-m", "PyInstaller", "--clean", spec],
        cwd=ROOT,
    )

def verify_output():
    exe_path = os.path.join(ROOT, "dist", "app.exe")
    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print(f"\n{'='*60}")
        print(f"  BAŞARILI! EXE oluşturuldu:")
        print(f"  {exe_path}")
        print(f"  Boyut: {size_mb:.1f} MB")
        print(f"{'='*60}\n")
    else:
        print("\n[HATA] dist/app.exe bulunamadı. Build başarısız olmuş olabilir.")
        sys.exit(1)

if __name__ == "__main__":
    print("=" * 60)
    print("  Muhasebe Beta – EXE Build Süreci")
    print("=" * 60)

    check_pyinstaller()
    check_dependencies()
    clean_build()
    build_exe()
    verify_output()
