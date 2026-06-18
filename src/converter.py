from pathlib import Path
from markitdown import MarkItDown


class PdfScanError(ValueError):
    """PDF khong co text layer -- can OCR."""
    pass


class DocumentConverter:
    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".xls", ".pptx", ".txt", ".html", ".htm"}

    def __init__(self):
        self._md = MarkItDown()

    def is_supported(self, file_path: str) -> bool:
        return Path(file_path).suffix.lower() in self.SUPPORTED_EXTENSIONS

    def _convert_pdf(self, input_path: Path, use_ocr: bool = False) -> str:
        import fitz
        doc = fitz.open(str(input_path))
        pages = []
        for i, page in enumerate(doc, start=1):
            text = page.get_text("text").strip()
            if text:
                pages.append(f"## Trang {i}\n\n{text}")
        doc.close()

        if pages:
            return "\n\n---\n\n".join(pages)

        # PDF scan: khong co text layer
        if use_ocr:
            from src.ocr_processor import ocr_pdf, OcrNotAvailableError
            try:
                result = ocr_pdf(str(input_path))
                if result:
                    return result
            except OcrNotAvailableError:
                raise
            except Exception as exc:
                raise PdfScanError(f"OCR that bai: {exc}")

        raise PdfScanError(
            "PDF khong co text layer (PDF scan). "
            "Bat OCR trong cai dat hoac cai Tesseract de xu ly loai file nay."
        )

    def convert_file(self, input_file: str, use_ocr: bool = False) -> str:
        input_path = Path(input_file)
        if not self.is_supported(str(input_path)):
            raise ValueError(f"Dinh dang khong duoc ho tro: {input_path.suffix}")
        if not input_path.is_file():
            raise FileNotFoundError(f"Khong tim thay file: {input_file}")
        if input_path.suffix.lower() == ".pdf":
            return self._convert_pdf(input_path, use_ocr=use_ocr)
        result = self._md.convert(str(input_path))
        return (result.text_content or "").strip()

    def save_markdown(self, markdown_text: str, output_file: str) -> None:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown_text, encoding="utf-8")

    def convert_and_save(self, input_file: str, output_file: str, use_ocr: bool = False) -> None:
        md = self.convert_file(input_file, use_ocr=use_ocr)
        self.save_markdown(md, output_file)
