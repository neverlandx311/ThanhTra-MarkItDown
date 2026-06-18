"""
build.py - Build ThanhTra-MarkItDown
Chay: python build.py  (can activate venv truoc hoac de script tu xu ly)
"""
import subprocess
import sys
import shutil
import glob
from pathlib import Path

ROOT = Path(__file__).parent
APP_NAME = "ThanhTra-MarkItDown"

# --- Luon dung Python trong .venv, khong dung system Python ---
VENV_PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
VENV_SITE   = ROOT / ".venv" / "Lib" / "site-packages"

if not VENV_PYTHON.exists():
    print(f"[LOI] Khong tim thay .venv. Chay: python -m venv .venv")
    sys.exit(1)


def run(cmd, **kwargs):
    """Chay lenh, raise neu loi."""
    result = subprocess.run(cmd, **kwargs)
    if result.returncode != 0:
        print(f"[LOI] Lenh that bai: {' '.join(str(c) for c in cmd)}")
        sys.exit(1)


def clean():
    for d in ["build", "dist", f"{APP_NAME}.spec"]:
        p = ROOT / d
        if p.exists():
            shutil.rmtree(p) if p.is_dir() else p.unlink()
            print(f"  Cleaned: {d}")


def fix_charset_normalizer():
    """
    charset_normalizer ban moi co file mypyc binary ten hash ngau nhien.
    PyInstaller khong gop duoc. Xoa file do de dung pure-Python fallback.
    Khong can download gi tu internet.
    """
    pattern = str(VENV_SITE / "charset_normalizer" / "*__mypyc*.pyd")
    files = glob.glob(pattern)
    if files:
        for f in files:
            Path(f).unlink()
            print(f"  Removed mypyc binary: {Path(f).name}")
    else:
        print("  charset_normalizer: no mypyc binaries found (OK)")


def build():
    icon = ROOT / "assets" / "icon.ico"

    cmd = [
        str(VENV_PYTHON), "-m", "PyInstaller",
        "--onedir",
        "--windowed",
        "--noconfirm",
        "--name", APP_NAME,
        "--paths", str(VENV_SITE),
        # Hidden imports
        "--hidden-import", "customtkinter",
        "--hidden-import", "markitdown",
        "--hidden-import", "fitz",
        "--hidden-import", "docx",
        "--hidden-import", "openpyxl",
        "--hidden-import", "pptx",
        "--hidden-import", "tkinter",
        "--hidden-import", "tkinter.ttk",
        "--hidden-import", "numpy",
        "--hidden-import", "charset_normalizer",
        "--hidden-import", "pdfminer",
        "--hidden-import", "pdfminer.high_level",
        "--hidden-import", "pdfminer.layout",
        "--hidden-import", "pdfminer.pdfpage",
        # Collect data files
        "--collect-all", "customtkinter",
        "--collect-all", "markitdown",
        "--collect-all", "magika",
        "--collect-all", "numpy",
        "--collect-all", "charset_normalizer",
        "--collect-all", "pdfminer",
        "--collect-all", "fitz",
        str(ROOT / "src" / "app.py"),
    ]

    if icon.exists():
        cmd += ["--icon", str(icon)]

    print(f"\nRunning PyInstaller (Python: {VENV_PYTHON})...")
    run(cmd, cwd=str(ROOT))

    exe = ROOT / "dist" / APP_NAME / f"{APP_NAME}.exe"
    if exe.exists():
        total_mb = sum(
            f.stat().st_size for f in (ROOT / "dist" / APP_NAME).rglob("*") if f.is_file()
        ) / 1024 / 1024
        print(f"\n[SUCCESS]")
        print(f"  EXE : {exe}")
        print(f"  Size: {total_mb:.0f} MB")
        print(f"\n  Phan phoi: copy ca thu muc dist\\{APP_NAME}\\ den may nguoi dung.")
    else:
        print("[LOI] Khong tim thay EXE.")
        sys.exit(1)


if __name__ == "__main__":
    print(f"=== Build {APP_NAME} ===\n")
    clean()
    fix_charset_normalizer()
    build()
