"""
zip_handler.py — Giải nén file ZIP trước khi chuyển đổi.

Tích hợp vào FolderProcessor: khi quét thư mục nguồn gặp file .zip,
tự động giải nén vào thư mục tạm cùng tên, rồi xử lý như thư mục thường.
Không cần thư viện ngoài (dùng zipfile chuẩn Python).
"""

import zipfile
import shutil
from pathlib import Path
from typing import Optional


class ZipExtractionError(Exception):
    """Lỗi khi giải nén file ZIP."""
    pass


class ZipHandler:
    """
    Giải nén các file .zip trong một thư mục vào thư mục tạm.
    Giữ nguyên cấu trúc thư mục bên trong ZIP.
    """

    def __init__(self, temp_base: Optional[Path] = None):
        """
        Args:
            temp_base: thư mục gốc chứa các thư mục tạm sau giải nén.
                       Mặc định: cùng thư mục với file ZIP (thêm suffix _unzipped).
        """
        self.temp_base = temp_base
        self._temp_dirs: list[Path] = []   # theo dõi để cleanup

    # ------------------------------------------------------------------

    def extract(self, zip_path: Path) -> Path:
        """
        Giải nén một file ZIP.

        Returns:
            Path thư mục chứa nội dung đã giải nén.
        Raises:
            ZipExtractionError nếu file không hợp lệ hoặc lỗi giải nén.
        """
        if not zipfile.is_zipfile(str(zip_path)):
            raise ZipExtractionError(f"Không phải file ZIP hợp lệ: {zip_path.name}")

        if self.temp_base:
            dest = Path(self.temp_base) / f"{zip_path.stem}_unzipped"
        else:
            dest = zip_path.parent / f"{zip_path.stem}_unzipped"

        # Nếu đã giải nén trước đó, xóa để giải nén lại
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True, exist_ok=True)

        try:
            with zipfile.ZipFile(str(zip_path), "r") as zf:
                # Bảo vệ path traversal (zip slip)
                for member in zf.infolist():
                    member_path = dest / member.filename
                    if not str(member_path.resolve()).startswith(str(dest.resolve())):
                        raise ZipExtractionError(
                            f"ZIP chứa đường dẫn không an toàn: {member.filename}"
                        )
                zf.extractall(str(dest))
        except zipfile.BadZipFile as e:
            shutil.rmtree(dest, ignore_errors=True)
            raise ZipExtractionError(f"File ZIP bị hỏng: {zip_path.name} — {e}")
        except Exception as e:
            shutil.rmtree(dest, ignore_errors=True)
            raise ZipExtractionError(f"Lỗi giải nén {zip_path.name}: {e}")

        self._temp_dirs.append(dest)
        return dest

    def extract_all_in_folder(self, folder: Path) -> list[tuple[Path, Path]]:
        """
        Tìm và giải nén tất cả file .zip trong folder (không đệ quy sâu — chỉ level 1).

        Returns:
            List của (zip_path, extracted_dir).
        """
        results = []
        for zip_path in sorted(folder.glob("*.zip")):
            try:
                extracted = self.extract(zip_path)
                results.append((zip_path, extracted))
            except ZipExtractionError:
                raise   # để caller xử lý
        return results

    def cleanup(self):
        """Xóa tất cả thư mục tạm đã tạo."""
        for d in self._temp_dirs:
            shutil.rmtree(d, ignore_errors=True)
        self._temp_dirs.clear()

    # Context manager
    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.cleanup()
