"""
test_markdown_aggregator.py — kiểm tra aggregate_markdown_files.
"""
from pathlib import Path
import pytest

from src.markdown_aggregator import aggregate_markdown_files


@pytest.fixture
def md_pair(tmp_path):
    """Tạo 2 file .md mẫu, trả về danh sách pairs."""
    f1 = tmp_path / "BaoCao.md"
    f2 = tmp_path / "KetLuan.md"
    f1.write_text("Nội dung báo cáo.", encoding="utf-8")
    f2.write_text("Nội dung kết luận.", encoding="utf-8")
    return [
        ("BaoCao.docx", str(f1)),
        ("KetLuan.pdf", str(f2)),
    ]


class TestAggregateMarkdownFiles:

    def test_creates_output_file(self, md_pair, tmp_path):
        out = tmp_path / "tong_hop.md"
        aggregate_markdown_files(md_pair, str(out))
        assert out.is_file()

    def test_contains_section_headers(self, md_pair, tmp_path):
        out = tmp_path / "tong_hop.md"
        aggregate_markdown_files(md_pair, str(out))
        content = out.read_text(encoding="utf-8")
        assert "# Tài liệu: BaoCao.docx" in content
        assert "# Tài liệu: KetLuan.pdf" in content

    def test_contains_source_label(self, md_pair, tmp_path):
        out = tmp_path / "tong_hop.md"
        aggregate_markdown_files(md_pair, str(out))
        content = out.read_text(encoding="utf-8")
        assert "Nguồn:" in content
        assert "BaoCao.docx" in content

    def test_contains_separator(self, md_pair, tmp_path):
        out = tmp_path / "tong_hop.md"
        aggregate_markdown_files(md_pair, str(out))
        content = out.read_text(encoding="utf-8")
        assert "=" * 50 in content

    def test_contains_file_content(self, md_pair, tmp_path):
        out = tmp_path / "tong_hop.md"
        aggregate_markdown_files(md_pair, str(out))
        content = out.read_text(encoding="utf-8")
        assert "Nội dung báo cáo." in content
        assert "Nội dung kết luận." in content

    def test_sections_in_order(self, md_pair, tmp_path):
        out = tmp_path / "tong_hop.md"
        aggregate_markdown_files(md_pair, str(out))
        content = out.read_text(encoding="utf-8")
        idx1 = content.index("BaoCao.docx")
        idx2 = content.index("KetLuan.pdf")
        assert idx1 < idx2

    def test_skips_missing_file(self, tmp_path):
        """File .md không tồn tại phải bị bỏ qua, không crash."""
        out = tmp_path / "out.md"
        pairs = [("ghost.docx", str(tmp_path / "nonexistent.md"))]
        aggregate_markdown_files(pairs, str(out))
        # Không crash, tạo file rỗng hoặc không tạo
        # (chấp nhận cả 2 hành vi)

    def test_creates_parent_dir(self, md_pair, tmp_path):
        out = tmp_path / "sub" / "deep" / "out.md"
        aggregate_markdown_files(md_pair, str(out))
        assert out.is_file()

    def test_with_source_root(self, tmp_path):
        """source_root làm relative path trong nhãn Nguồn."""
        src_root = tmp_path / "src"
        src_root.mkdir()
        md = tmp_path / "BaoCao.md"
        md.write_text("nội dung", encoding="utf-8")
        orig = src_root / "subfolder" / "BaoCao.docx"

        out = tmp_path / "out.md"
        aggregate_markdown_files(
            [(str(orig), str(md))],
            str(out),
            source_root=str(src_root),
        )
        content = out.read_text(encoding="utf-8")
        assert "subfolder" in content
