"""
test_folder_processor.py — kiểm tra FolderProcessor.
"""

import tempfile
import os
from pathlib import Path

import pytest

from src.logger import ConversionLogger
from src.folder_processor import FolderProcessor


@pytest.fixture
def tmp_log(tmp_path):
    """Logger ghi vào file tạm."""
    log_file = tmp_path / "test.log"
    return ConversionLogger(str(log_file))


@pytest.fixture
def processor(tmp_log):
    return FolderProcessor(logger=tmp_log)


@pytest.fixture
def sample_folder(tmp_path):
    """
    Tạo thư mục mẫu:
        sample/
            BaoCao.txt
            KetLuan.txt
            PhuLuc/
                BangTinh.txt
    """
    root = tmp_path / "sample"
    (root / "PhuLuc").mkdir(parents=True)

    (root / "BaoCao.txt").write_text(
        "Báo cáo kết quả thanh tra năm 2024.", encoding="utf-8"
    )
    (root / "KetLuan.txt").write_text(
        "Kết luận thanh tra số 01/KL-TTr.", encoding="utf-8"
    )
    (root / "PhuLuc" / "BangTinh.txt").write_text(
        "Phụ lục bảng tính.", encoding="utf-8"
    )
    return root


# ------------------------------------------------------------------
# scan_supported_files
# ------------------------------------------------------------------

class TestScanSupportedFiles:

    def test_finds_txt_files(self, processor, sample_folder):
        files = processor.scan_supported_files(str(sample_folder))
        names = {f.name for f in files}
        assert "BaoCao.txt" in names
        assert "KetLuan.txt" in names
        assert "BangTinh.txt" in names

    def test_ignores_unsupported(self, processor, sample_folder):
        # Tạo file không hỗ trợ
        (sample_folder / "image.png").write_bytes(b"\x89PNG")
        files = processor.scan_supported_files(str(sample_folder))
        names = {f.name for f in files}
        assert "image.png" not in names

    def test_empty_folder_returns_empty(self, processor, tmp_path):
        empty = tmp_path / "empty"
        empty.mkdir()
        assert processor.scan_supported_files(str(empty)) == []


# ------------------------------------------------------------------
# convert_folder
# ------------------------------------------------------------------

class TestConvertFolder:

    def test_converts_all_files(self, processor, sample_folder, tmp_path):
        out = tmp_path / "output"
        stats = processor.convert_folder(str(sample_folder), str(out))

        assert stats["total"] == 3
        assert stats["success"] == 3
        assert stats["failed"] == 0

    def test_preserves_directory_structure(self, processor, sample_folder, tmp_path):
        out = tmp_path / "output"
        processor.convert_folder(str(sample_folder), str(out))

        assert (out / "BaoCao.md").is_file()
        assert (out / "KetLuan.md").is_file()
        assert (out / "PhuLuc" / "BangTinh.md").is_file()

    def test_output_is_markdown_text(self, processor, sample_folder, tmp_path):
        out = tmp_path / "output"
        processor.convert_folder(str(sample_folder), str(out))

        content = (out / "BaoCao.md").read_text(encoding="utf-8")
        assert len(content) > 0

    def test_creates_output_dir_if_missing(self, processor, sample_folder, tmp_path):
        out = tmp_path / "does_not_exist" / "nested"
        processor.convert_folder(str(sample_folder), str(out))
        assert out.is_dir()

    def test_progress_callback_called(self, tmp_log, sample_folder, tmp_path):
        calls = []

        def on_progress(current, total, filename):
            calls.append((current, total, filename))

        proc = FolderProcessor(logger=tmp_log, progress_callback=on_progress)
        out = tmp_path / "output"
        proc.convert_folder(str(sample_folder), str(out))

        assert len(calls) == 3
        # current đi từ 1 → 3
        assert calls[0][0] == 1
        assert calls[-1][0] == 3

    def test_stats_converted_pairs(self, processor, sample_folder, tmp_path):
        out = tmp_path / "output"
        stats = processor.convert_folder(str(sample_folder), str(out))

        assert len(stats["converted_pairs"]) == 3
        for src, dst in stats["converted_pairs"]:
            assert Path(dst).suffix == ".md"

    def test_processor_does_not_crash_on_bad_input(self, tmp_log, tmp_path):
        """Processor phải xử lý file hỏng mà không crash — success hoặc failed đều OK."""
        src = tmp_path / "src"
        src.mkdir()
        broken = src / "broken.docx"
        broken.write_bytes(b"not a real docx")

        out = tmp_path / "out"
        proc = FolderProcessor(logger=tmp_log)
        stats = proc.convert_folder(str(src), str(out))

        # Không crash và đếm đúng tổng
        assert stats["total"] == 1
        assert stats["success"] + stats["failed"] == 1


# ------------------------------------------------------------------
# Logger ghi đúng
# ------------------------------------------------------------------

class TestLogger:

    def test_log_success_written(self, tmp_path, sample_folder):
        log_file = tmp_path / "run.log"
        logger = ConversionLogger(str(log_file))
        proc = FolderProcessor(logger=logger)
        out = tmp_path / "out"

        proc.convert_folder(str(sample_folder), str(out))

        log_content = log_file.read_text(encoding="utf-8")
        assert "SUCCESS" in log_content
        assert "BaoCao" in log_content
