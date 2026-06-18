from pathlib import Path
from markitdown import MarkItDown


class PdfScanError(ValueError):
    """PDF không có text layer — cần OCR."""
    pass


class DocumentConverter:
    """
    Chuyển đổi tài liệu sang Markdown.
    - PDF: dùng PyMuPDF (fitz) trực tiếp — không phụ thuộc pdfminer
    - DOCX/XLSX/PPTX/TXT/HTML: dùng MarkItDown
    """

    SUPPORTED_EXTENSIONS = {
        ".pdf",
        ".docx",
        ".xlsx",
        ".xls",
        ".pptx",
        ".txt",
        ".html",
        ".htm",
    }

    def __init__(self):
        self._md = MarkItDown()

    def is_supported(self, file_path: str) -> bool:
        """Kiểm tra định dạng file có được hỗ trợ không."""
        ext = Path(file_path).suffix.lower()
        return ext in self.SUPPORTED_EXTENSIONS

    def _convert_pdf(self, input_path: Path) -> str:
        """Dùng PyMuPDF để extract text từ PDF có text layer."""
        import fitz  # PyMuPDF
        doc = fitz.open(str(input_path))
        pages = []
        for i, page in enumerate(doc, start=1):
            text = page.get_text("text").strip()
            if text:
                pages.append(f"## Trang {i}\n\n{text}")
        doc.close()
        if not pages:
            raise PdfScanError(
                "PDF không có text layer (PDF scan). "
                "Tính năng OCR sẽ có ở phiên bản 2.0."
            )
        return "\n\n---\n\n".join(pages)

    def convert_file(self, input_file: str) -> str:
        """
        Chuyển đổi file → chuỗi Markdown.
        Raises ValueError nếu định dạng không hỗ trợ.
        Raises FileNotFoundError nếu không tìm thấy file.
        """
        input_path = Path(input_file)

        if not self.is_supported(str(input_path)):
            raise ValueError(
                f"Định dạng không được hỗ trợ: {input_path.suffix}"
            )

        if not input_path.is_file():
            raise FileNotFoundError(f"Không tìm thấy file: {input_file}")

        ext = input_path.suffix.lower()

        # PDF: dùng PyMuPDF trực tiếp
        if ext == ".pdf":
            return self._convert_pdf(input_path)

        # Các định dạng khác: dùng MarkItDown
        result = self._md.convert(str(input_path))
        content = result.text_content or ""
        return content.strip()

    def save_markdown(self, markdown_text: str, output_file: str) -> None:
        """Ghi nội dung Markdown ra file, tự tạo thư mục nếu chưa có."""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown_text, encoding="utf-8")

    def convert_and_save(self, input_file: str, output_file: str) -> None:
        """Chuyển đổi và lưu file Markdown trong một bước."""
        md = self.convert_file(input_file)
        self.save_markdown(md, output_file)