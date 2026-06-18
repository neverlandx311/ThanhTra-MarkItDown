"""
test_prompt_generator.py — kiểm tra generate_prompt_file.
"""
from pathlib import Path
import pytest

from src.prompt_generator import generate_prompt_file


class TestGeneratePromptFile:

    def test_creates_file(self, tmp_path):
        path = generate_prompt_file(str(tmp_path), doc_count=3)
        assert Path(path).is_file()

    def test_filename_is_prompt_md(self, tmp_path):
        path = generate_prompt_file(str(tmp_path), doc_count=1)
        assert Path(path).name == "_prompt.md"

    def test_contains_doc_count(self, tmp_path):
        path = generate_prompt_file(str(tmp_path), doc_count=7)
        content = Path(path).read_text(encoding="utf-8")
        assert "7" in content

    def test_contains_folder_name(self, tmp_path):
        path = generate_prompt_file(str(tmp_path), doc_count=2, folder_name="HoSoKL30")
        content = Path(path).read_text(encoding="utf-8")
        assert "HoSoKL30" in content

    def test_contains_version(self, tmp_path):
        path = generate_prompt_file(str(tmp_path), doc_count=1, version="v9.9")
        content = Path(path).read_text(encoding="utf-8")
        assert "v9.9" in content

    def test_contains_prompt_suggestions(self, tmp_path):
        path = generate_prompt_file(str(tmp_path), doc_count=1)
        content = Path(path).read_text(encoding="utf-8")
        assert "ChatGPT" in content
        assert "NotebookLM" in content

    def test_creates_parent_dir(self, tmp_path):
        nested = tmp_path / "a" / "b"
        path = generate_prompt_file(str(nested), doc_count=1)
        assert Path(path).is_file()

    def test_utf8_encoding(self, tmp_path):
        path = generate_prompt_file(str(tmp_path), doc_count=1)
        content = Path(path).read_text(encoding="utf-8")
        assert "Thanh tra" in content
