"""
test_ocr_processor.py -- kiem tra ocr_processor va OCR fallback trong converter.
OCR chi chay neu Tesseract duoc cai dat (skip neu khong co).
"""
import pytest
from pathlib import Path

from src.ocr_processor import is_ocr_available, OcrNotAvailableError
from src.converter import DocumentConverter, PdfScanError

HAS_TESSERACT = is_ocr_available()


class TestOcrAvailability:

    def test_is_ocr_available_returns_bool(self):
        result = is_ocr_available()
        assert isinstance(result, bool)

    def test_ocr_not_available_error_is_runtime_error(self):
        assert issubclass(OcrNotAvailableError, RuntimeError)


class TestConverterOcrFlag:

    def test_pdf_scan_without_ocr_raises_pdf_scan_error(self, tmp_path):
        """PDF scan + use_ocr=False (mac dinh) -> PdfScanError."""
        import fitz
        doc = fitz.open()
        doc.new_page()
        pdf = tmp_path / "blank.pdf"
        doc.save(str(pdf))
        doc.close()

        conv = DocumentConverter()
        with pytest.raises(PdfScanError):
            conv.convert_file(str(pdf), use_ocr=False)

    @pytest.mark.skipif(not HAS_TESSERACT, reason="Tesseract chua duoc cai dat")
    def test_pdf_scan_with_ocr_returns_string(self, tmp_path):
        """PDF scan + use_ocr=True + Tesseract co san -> tra ve string."""
        import fitz
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Hello OCR test")
        pdf = tmp_path / "scan_sim.pdf"
        doc.save(str(pdf))
        doc.close()

        conv = DocumentConverter()
        result = conv.convert_file(str(pdf), use_ocr=True)
        assert isinstance(result, str)

    def test_use_ocr_false_is_default(self, tmp_path):
        """use_ocr mac dinh la False -- PDF scan van raise PdfScanError."""
        import fitz
        doc = fitz.open()
        doc.new_page()
        pdf = tmp_path / "blank2.pdf"
        doc.save(str(pdf))
        doc.close()

        conv = DocumentConverter()
        with pytest.raises(PdfScanError):
            conv.convert_file(str(pdf))  # khong truyen use_ocr

    @pytest.mark.skipif(not HAS_TESSERACT, reason="Tesseract chua duoc cai dat")
    def test_ocr_pdf_direct(self, tmp_path):
        """Goi truc tiep ocr_pdf() neu Tesseract co san."""
        from src.ocr_processor import ocr_pdf
        import fitz
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Test OCR direct call")
        pdf = tmp_path / "direct.pdf"
        doc.save(str(pdf))
        doc.close()

        result = ocr_pdf(str(pdf))
        assert isinstance(result, str)
