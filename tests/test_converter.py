"""
test_converter.py — kiểm tra DocumentConverter.
Dùng file tạm thật (không mock MarkItDown) để đảm bảo tích hợp thực.
"""

import tempfile
import os
from pathlib import Path

import pytest

from src.converter import DocumentConverter


@pytest.fixture
def conv():
    return DocumentConverter()


# ------------------------------------------------------------------
# is_supported
# ------------------------------------------------------------------

class TestIsSupported:

    def test_pdf_supported(self, conv):
        assert conv.is_supported("report.pdf") is True

    def test_docx_supported(self, conv):
        assert conv.is_supported("file.docx") is True

    def test_xlsx_supported(self, conv):
        assert conv.is_supported("bang.xlsx") is True

    def test_pptx_supported(self, conv):
        assert conv.is_supported("slide.pptx") is True

    def test_txt_supported(self, conv):
        assert conv.is_supported("note.txt") is True

    def test_html_supported(self, conv):
        assert conv.is_supported("page.html") is True

    def test_exe_not_supported(self, conv):
        assert conv.is_supported("setup.exe") is False

    def test_png_not_supported(self, conv):
        assert conv.is_supported("image.png") is False

    def test_case_insensitive(self, conv):
        assert conv.is_supported("FILE.PDF") is True
        assert conv.is_supported("FILE.DOCX") is True


# ------------------------------------------------------------------
# convert_file — với file .txt thật
# ------------------------------------------------------------------

class TestConvertFile:

    def test_convert_txt_returns_string(self, conv):
        with tempfile.NamedTemporaryFile(
            suffix=".txt", mode="w", delete=False, encoding="utf-8"
        ) as f:
            f.write("Xin chào thế giới\nĐây là nội dung test.")
            tmp = f.name
        try:
            result = conv.convert_file(tmp)
            assert isinstance(result, str)
            assert "Xin chào" in result or len(result) > 0
        finally:
            os.unlink(tmp)

    def test_convert_unsupported_raises_value_error(self, conv):
        with pytest.raises(ValueError, match="không được hỗ trợ"):
            conv.convert_file("file.zip")

    def test_convert_missing_file_raises(self, conv):
        with pytest.raises(FileNotFoundError):
            conv.convert_file("/nonexistent/path/file.txt")

    def test_convert_html_basic(self, conv):
        html_content = "<html><body><h1>Tiêu đề</h1><p>Nội dung.</p></body></html>"
        with tempfile.NamedTemporaryFile(
            suffix=".html", mode="w", delete=False, encoding="utf-8"
        ) as f:
            f.write(html_content)
            tmp = f.name
        try:
            result = conv.convert_file(tmp)
            assert isinstance(result, str)
            assert len(result) > 0
        finally:
            os.unlink(tmp)


# ------------------------------------------------------------------
# convert_and_save
# ------------------------------------------------------------------

class TestConvertAndSave:

    def test_creates_output_file(self, conv, tmp_path):
        src = tmp_path / "input.txt"
        src.write_text("Hello MarkItDown", encoding="utf-8")
        out = tmp_path / "subdir" / "output.md"

        conv.convert_and_save(str(src), str(out))

        assert out.is_file()
        content = out.read_text(encoding="utf-8")
        assert len(content) > 0

    def test_creates_nested_output_dir(self, conv, tmp_path):
        src = tmp_path / "doc.txt"
        src.write_text("test", encoding="utf-8")
        out = tmp_path / "a" / "b" / "c" / "doc.md"

        conv.convert_and_save(str(src), str(out))
        assert out.is_file()
