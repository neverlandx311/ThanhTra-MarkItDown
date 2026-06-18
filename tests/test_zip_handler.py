"""
test_zip_handler.py -- kiem tra ZipHandler va tich hop ZIP vao FolderProcessor.
"""
import zipfile
import tempfile
from pathlib import Path
import pytest

from src.zip_handler import ZipHandler, ZipExtractionError
from src.folder_processor import FolderProcessor
from src.logger import ConversionLogger


# --- Fixtures ----------------------------------------------------------------

@pytest.fixture
def simple_zip(tmp_path) -> Path:
    """ZIP chua 2 file .txt."""
    zp = tmp_path / "HoSo.zip"
    with zipfile.ZipFile(str(zp), "w") as zf:
        zf.writestr("BaoCao.txt", "Noi dung bao cao")
        zf.writestr("KetLuan.txt", "Noi dung ket luan")
    return zp


@pytest.fixture
def nested_zip(tmp_path) -> Path:
    """ZIP co thu muc con ben trong."""
    zp = tmp_path / "Archive.zip"
    with zipfile.ZipFile(str(zp), "w") as zf:
        zf.writestr("sub/BaoCao.txt", "Noi dung bao cao")
        zf.writestr("PhuLuc.txt", "Noi dung phu luc")
    return zp


@pytest.fixture
def bad_zip(tmp_path) -> Path:
    """File khong phai ZIP nhung co duoi .zip."""
    zp = tmp_path / "fake.zip"
    zp.write_bytes(b"this is not a zip file")
    return zp


def _temp_base() -> Path:
    """Tao thu muc tam that su (ngoai pytest tmp_path) de tranh van de mount."""
    return Path(tempfile.mkdtemp())


# --- ZipHandler --------------------------------------------------------------

class TestZipHandler:

    def test_extract_creates_dir(self, simple_zip):
        base = _temp_base()
        zh = ZipHandler(temp_base=base)
        dest = zh.extract(simple_zip)
        assert dest.is_dir()
        zh.cleanup()

    def test_extract_files_present(self, simple_zip):
        with ZipHandler(temp_base=_temp_base()) as zh:
            dest = zh.extract(simple_zip)
            files = list(dest.rglob("*.txt"))
        assert len(files) == 2

    def test_extract_nested_structure(self, nested_zip):
        with ZipHandler(temp_base=_temp_base()) as zh:
            dest = zh.extract(nested_zip)
            all_txt = list(dest.rglob("*.txt"))
        assert len(all_txt) == 2
        names = {f.name for f in all_txt}
        assert "BaoCao.txt" in names
        assert "PhuLuc.txt" in names

    def test_bad_zip_raises(self, bad_zip):
        with ZipHandler(temp_base=_temp_base()) as zh:
            with pytest.raises(ZipExtractionError):
                zh.extract(bad_zip)

    def test_cleanup_removes_temp_dirs(self, simple_zip):
        base = _temp_base()
        zh = ZipHandler(temp_base=base)
        dest = zh.extract(simple_zip)
        assert dest.is_dir()
        zh.cleanup()
        assert not dest.exists()

    def test_context_manager_cleans_up(self, simple_zip):
        base = _temp_base()
        with ZipHandler(temp_base=base) as zh:
            dest = zh.extract(simple_zip)
        assert not dest.exists()

    def test_extract_all_in_folder(self, tmp_path, simple_zip, nested_zip):
        # simple_zip va nested_zip da nam trong tmp_path
        with ZipHandler(temp_base=_temp_base()) as zh:
            results = zh.extract_all_in_folder(tmp_path)
        assert len(results) == 2

    def test_extract_all_ignores_non_zip(self, tmp_path):
        (tmp_path / "doc.txt").write_text("text")
        (tmp_path / "data.pdf").write_bytes(b"%PDF")
        with ZipHandler(temp_base=_temp_base()) as zh:
            results = zh.extract_all_in_folder(tmp_path)
        assert results == []

    def test_dest_named_after_zip(self, simple_zip):
        base = _temp_base()
        zh = ZipHandler(temp_base=base)
        dest = zh.extract(simple_zip)
        assert "HoSo" in dest.name
        zh.cleanup()


# --- Tich hop ZIP voi FolderProcessor ----------------------------------------

class TestFolderProcessorZip:

    def _make_logger(self, tmp_path) -> ConversionLogger:
        return ConversionLogger(str(tmp_path / "test.log"))

    def test_zip_files_converted(self, tmp_path):
        """File ben trong ZIP phai duoc chuyen doi thanh .md."""
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()

        zp = src / "HoSo.zip"
        with zipfile.ZipFile(str(zp), "w") as zf:
            zf.writestr("BaoCao.txt", "Noi dung bao cao can chuyen doi")
            zf.writestr("KetLuan.txt", "Noi dung ket luan can chuyen doi")

        processor = FolderProcessor(logger=self._make_logger(tmp_path))
        stats = processor.convert_folder(str(src), str(dst))

        assert stats["success"] == 2
        assert stats["failed"] == 0

    def test_zip_output_in_subfolder(self, tmp_path):
        """File tu HoSo.zip phai ra thu muc dst/HoSo/."""
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()

        zp = src / "HoSo.zip"
        with zipfile.ZipFile(str(zp), "w") as zf:
            zf.writestr("BaoCao.txt", "noi dung")

        processor = FolderProcessor(logger=self._make_logger(tmp_path))
        processor.convert_folder(str(src), str(dst))

        assert (dst / "HoSo" / "BaoCao.md").is_file()

    def test_mix_zip_and_plain_files(self, tmp_path):
        """Thu muc co ca file thuong lan ZIP -- ca hai deu duoc chuyen doi."""
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()

        (src / "TaiLieu.txt").write_text("file thuong")

        zp = src / "Archive.zip"
        with zipfile.ZipFile(str(zp), "w") as zf:
            zf.writestr("BaoCao.txt", "file trong zip")

        processor = FolderProcessor(logger=self._make_logger(tmp_path))
        stats = processor.convert_folder(str(src), str(dst))

        assert stats["success"] == 2

    def test_no_zip_unmodified_behavior(self, tmp_path):
        """Khong co ZIP thi hoat dong y nhu cu."""
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()
        (src / "A.txt").write_text("noi dung A")
        (src / "B.txt").write_text("noi dung B")

        processor = FolderProcessor(logger=self._make_logger(tmp_path))
        stats = processor.convert_folder(str(src), str(dst))

        assert stats["success"] == 2
        assert (dst / "A.md").is_file()
        assert (dst / "B.md").is_file()
