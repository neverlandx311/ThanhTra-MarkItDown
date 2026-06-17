from pathlib import Path
from markitdown import MarkItDown


class DocumentConverter:
    """
    Chuyển đổi tài liệu sang Markdown bằng MarkItDown
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
        self.converter = MarkItDown()

    def is_supported(self, file_path: str) -> bool:
        """
        Kiểm tra file có được hỗ trợ không
        """
        ext = Path(file_path).suffix.lower()
        return ext in self.SUPPORTED_EXTENSIONS

    def convert_file(self, input_file: str) -> str:
        """
        Trả về nội dung markdown
        """

        if not self.is_supported(input_file):
            raise ValueError(
                f"Định dạng không được hỗ trợ: {input_file}"
            )

        result = self.converter.convert(input_file)

        return result.text_content

    def save_markdown(
        self,
        markdown_text: str,
        output_file: str
    ):

        output_path = Path(output_file)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            output_path,
            "w",
            encoding="utf-8"
        ) as f:
            f.write(markdown_text)

    def convert_and_save(
        self,
        input_file: str,
        output_file: str
    ):
        """
        Chuyển đổi và ghi file
        """

        md = self.convert_file(input_file)

        self.save_markdown(
            md,
            output_file
        )