from pathlib import Path
from typing import Callable, Optional

from src.converter import DocumentConverter, PdfScanError
from src.logger import ConversionLogger


class FolderProcessor:
    """
    Xử lý chuyển đổi toàn bộ thư mục hồ sơ.
    Giữ nguyên cấu trúc thư mục ở output.
    """

    def __init__(
        self,
        logger: ConversionLogger,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ):
        """
        Args:
            logger: ConversionLogger để ghi log.
            progress_callback: hàm (current, total, filename) → None
                               dùng cho GUI cập nhật progress bar.
        """
        self.converter = DocumentConverter()
        self.logger = logger
        self.progress_callback = progress_callback

    # ------------------------------------------------------------------
    # Quét file
    # ------------------------------------------------------------------

    def scan_supported_files(self, source_folder: str) -> list[Path]:
        """Trả về danh sách Path các file được hỗ trợ (đệ quy)."""
        source_path = Path(source_folder)
        return sorted(
            f
            for f in source_path.rglob("*")
            if f.is_file() and self.converter.is_supported(str(f))
        )

    # ------------------------------------------------------------------
    # Chuyển đổi
    # ------------------------------------------------------------------

    def convert_folder(
        self,
        source_folder: str,
        output_folder: str,
    ) -> dict:
        """
        Chuyển đổi toàn bộ thư mục, giữ nguyên cấu trúc thư mục con.

        Returns:
            dict với các khoá: total, success, failed, skipped,
                               converted_pairs [(src_path, out_md_path)]
        """
        source_path = Path(source_folder)
        output_path = Path(output_folder)
        output_path.mkdir(parents=True, exist_ok=True)

        stats: dict = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "converted_pairs": [],   # [(str input, str output_md)]
        }

        files = self.scan_supported_files(source_folder)
        stats["total"] = len(files)

        for idx, file_path in enumerate(files, start=1):

            # Thông báo progress cho GUI
            if self.progress_callback:
                self.progress_callback(idx, stats["total"], file_path.name)

            try:
                relative = file_path.relative_to(source_path)
                output_md = (output_path / relative).with_suffix(".md")

                self.converter.convert_and_save(
                    str(file_path),
                    str(output_md),
                )

                self.logger.success(str(relative))
                stats["success"] += 1
                stats["converted_pairs"].append(
                    (str(file_path), str(output_md))
                )

            except PdfScanError as exc:
                self.logger.skipped(f"{file_path.name} — {exc}")
                stats["skipped"] += 1

            except Exception as exc:
                self.logger.error(f"{file_path.name} — {exc}")
                stats["failed"] += 1

        return stats
