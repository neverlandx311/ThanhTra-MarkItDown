"""
ocr_processor.py -- OCR cho PDF scan (khong co text layer).

Su dung:
    PyMuPDF  -- render tung trang PDF thanh anh PNG (da co san trong requirements)
    pytesseract + Tesseract -- OCR tren anh
    Ngon ngu: vie+eng (tieng Viet + tieng Anh)

Tesseract phai duoc cai dat rieng:
    https://github.com/UB-Mannheim/tesseract/wiki  (Windows installer)
    Sau do them vao PATH hoac dat TESSERACT_CMD.

pytesseract la optional -- neu chua cai thi bao loi ro rang.
"""

import io
from pathlib import Path
from typing import Optional


# Thu TESSERACT_CMD tu bien moi truong hoac duong dan mac dinh Windows
import os
_DEFAULT_TESSERACT = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


class OcrNotAvailableError(RuntimeError):
    """Raise khi pytesseract hoac Tesseract chua duoc cai dat."""
    pass


def _get_pytesseract():
    """Import pytesseract, raise OcrNotAvailableError neu chua cai."""
    try:
        import pytesseract
        # Neu bien moi truong TESSERACT_CMD duoc dat, dung no
        env_cmd = os.environ.get("TESSERACT_CMD", "")
        if env_cmd:
            pytesseract.pytesseract.tesseract_cmd = env_cmd
        elif Path(_DEFAULT_TESSERACT).exists():
            pytesseract.pytesseract.tesseract_cmd = _DEFAULT_TESSERACT
        return pytesseract
    except ImportError:
        raise OcrNotAvailableError(
            "Chua cai dat pytesseract.\n"
            "Chay: pip install pytesseract\n"
            "Va cai Tesseract tai: https://github.com/UB-Mannheim/tesseract/wiki"
        )


def _check_tesseract(pytesseract_mod) -> None:
    """Kiem tra Tesseract co chay duoc khong."""
    try:
        pytesseract_mod.get_tesseract_version()
    except Exception:
        raise OcrNotAvailableError(
            "Khong tim thay Tesseract OCR.\n"
            "Tai va cai dat tai: https://github.com/UB-Mannheim/tesseract/wiki\n"
            "Sau do them vao PATH hoac dat bien moi truong TESSERACT_CMD."
        )


def is_ocr_available() -> bool:
    """Kiem tra nhanh xem OCR co san sang su dung khong."""
    try:
        pt = _get_pytesseract()
        _check_tesseract(pt)
        return True
    except OcrNotAvailableError:
        return False


def ocr_pdf(pdf_path: str, lang: str = "vie+eng", dpi: int = 300) -> str:
    """
    OCR mot file PDF scan, tra ve chuoi Markdown.

    Args:
        pdf_path: duong dan file PDF.
        lang: ngon ngu Tesseract (mac dinh 'vie+eng').
        dpi: do phan giai render anh (mac dinh 300).

    Returns:
        Chuoi Markdown chua ket qua OCR.

    Raises:
        OcrNotAvailableError: neu pytesseract/Tesseract chua duoc cai dat.
        FileNotFoundError: neu file khong ton tai.
        ValueError: neu file khong phai PDF hop le.
    """
    import fitz  # PyMuPDF

    pt = _get_pytesseract()
    _check_tesseract(pt)

    pdf_path = Path(pdf_path)
    if not pdf_path.is_file():
        raise FileNotFoundError(f"Khong tim thay file: {pdf_path}")

    try:
        doc = fitz.open(str(pdf_path))
    except Exception as exc:
        raise ValueError(f"Khong the mo PDF: {exc}")

    pages_md: list[str] = []
    mat = fitz.Matrix(dpi / 72, dpi / 72)  # scale factor

    for i, page in enumerate(doc, start=1):
        # Render trang thanh anh PNG
        pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
        img_bytes = pix.tobytes("png")

        # OCR tren anh
        try:
            from PIL import Image as PILImage
            img = PILImage.open(io.BytesIO(img_bytes))
            text = pt.image_to_string(img, lang=lang, config="--psm 3")
        except ImportError:
            # Fallback: dung pytesseract.image_to_string voi bytes truc tiep
            text = pt.image_to_string(img_bytes, lang=lang, config="--psm 3")

        text = text.strip()
        if text:
            pages_md.append(f"## Trang {i}\n\n{text}")

    doc.close()

    if not pages_md:
        return ""

    return "\n\n---\n\n".join(pages_md)
