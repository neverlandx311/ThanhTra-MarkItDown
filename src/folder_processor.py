import tempfile
from pathlib import Path
from typing import Callable, Optional

from src.converter import DocumentConverter, PdfScanError
from src.logger import ConversionLogger
from src.zip_handler import ZipHandler, ZipExtractionError


class FolderProcessor:
    def __init__(self, logger, progress_callback=None, use_ocr: bool = False):
        self.converter = DocumentConverter()
        self.logger = logger
        self.progress_callback = progress_callback
        self.use_ocr = use_ocr

    def scan_supported_files(self, source_folder: str) -> list:
        source_path = Path(source_folder)
        return sorted(
            f for f in source_path.rglob("*")
            if f.is_file() and self.converter.is_supported(str(f))
        )

    def convert_folder(self, source_folder: str, output_folder: str) -> dict:
        source_path = Path(source_folder)
        output_path = Path(output_folder)
        output_path.mkdir(parents=True, exist_ok=True)

        stats = {"total": 0, "success": 0, "failed": 0, "skipped": 0, "converted_pairs": []}
        file_tasks = []  # (file_path, scan_root, output_root)

        with ZipHandler(temp_base=Path(tempfile.mkdtemp())) as zh:

            # 1. File trong source_folder (khong phai .zip)
            for f in self.scan_supported_files(str(source_path)):
                file_tasks.append((f, source_path, output_path))

            # 2. Giai nen ZIP
            for zip_path in sorted(source_path.glob("*.zip")):
                try:
                    extracted_dir = zh.extract(zip_path)
                    self.logger.success(f"[ZIP] {zip_path.name} -> {extracted_dir.name}/")
                    zip_out = output_path / zip_path.stem
                    for f in self.scan_supported_files(str(extracted_dir)):
                        file_tasks.append((f, extracted_dir, zip_out))
                except ZipExtractionError as exc:
                    self.logger.error(f"[ZIP] {exc}")
                    stats["failed"] += 1

            stats["total"] = len(file_tasks)

            for idx, (file_path, scan_root, out_root) in enumerate(file_tasks, start=1):
                if self.progress_callback:
                    self.progress_callback(idx, stats["total"], file_path.name)
                try:
                    relative = file_path.relative_to(scan_root)
                    output_md = (out_root / relative).with_suffix(".md")
                    self.converter.convert_and_save(
                        str(file_path), str(output_md), use_ocr=self.use_ocr
                    )
                    self.logger.success(str(relative))
                    stats["success"] += 1
                    stats["converted_pairs"].append((str(file_path), str(output_md)))
                except PdfScanError as exc:
                    self.logger.skipped(f"{file_path.name} -- {exc}")
                    stats["skipped"] += 1
                except PermissionError:
                    self.logger.error(
                        f"{file_path.name} -- File dang bi khoa (Word/Excel dang mo)."
                    )
                    stats["failed"] += 1
                except Exception as exc:
                    self.logger.error(f"{file_path.name} -- {exc}")
                    stats["failed"] += 1

        return stats
