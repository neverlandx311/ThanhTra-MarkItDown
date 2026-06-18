"""
markdown_aggregator.py
Ghép nhiều file Markdown thành một file tổng hợp,
theo định dạng chuẩn để upload NotebookLM / ChatGPT / Claude.

Định dạng output:

    # Tài liệu: BaoCao.docx

    Nguồn:
    BaoCao.docx

    ---

    (nội dung markdown)

    ==================================================

    # Tài liệu: KetLuan.pdf
    ...
"""

from pathlib import Path
from typing import List, Optional


SEPARATOR = "=" * 50


def aggregate_markdown_files(
    md_pairs: List[tuple],
    output_path: str,
    source_root: Optional[str] = None,
) -> None:
    """
    Gộp danh sách file Markdown thành một file tổng hợp.

    Args:
        md_pairs: danh sách tuple (original_filename, md_file_path)
                  hoặc chỉ (md_file_path,) — khi đó dùng tên file làm tiêu đề.
        output_path: đường dẫn file output tổng hợp.
        source_root: nếu cung cấp, hiển thị relative path từ root này.
    """
    sections: List[str] = []

    for item in md_pairs:
        # Hỗ trợ 2 dạng: tuple (orig, md) hoặc chỉ md_path
        if isinstance(item, (list, tuple)) and len(item) == 2:
            orig_name, md_path = item
        else:
            md_path = item
            orig_name = Path(str(item)).name

        md_path = Path(md_path)

        if not md_path.is_file():
            continue

        content = md_path.read_text(encoding="utf-8").strip()

        # Xác định label nguồn
        orig_path = Path(orig_name)
        if source_root:
            try:
                orig_label = str(orig_path.relative_to(source_root))
            except ValueError:
                orig_label = orig_path.name
        else:
            orig_label = orig_path.name

        section = (
            f"# Tài liệu: {orig_path.name}\n"
            f"\n"
            f"Nguồn:\n"
            f"{orig_label}\n"
            f"\n"
            f"---\n"
            f"\n"
            f"{content}\n"
            f"\n"
            f"{SEPARATOR}"
        )
        sections.append(section)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n\n".join(sections) + "\n", encoding="utf-8")


def aggregate_from_folder(
    source_folder: str,
    output_folder: str,
    output_filename: str = "_tong_hop.md",
) -> str:
    """
    Tiện ích: quét toàn bộ file .md trong output_folder,
    ghép thành một file tổng hợp.
    Trả về đường dẫn file tổng hợp.
    """
    out_root = Path(output_folder)
    md_files = sorted(
        f for f in out_root.rglob("*.md")
        if f.name != output_filename
    )

    src_root = Path(source_folder)

    pairs = []
    for md_file in md_files:
        # Xác định file gốc từ relative path
        relative = md_file.relative_to(out_root)
        # Tái tạo tên file gốc (chưa biết extension, dùng tên .md thay thế)
        orig_guess = src_root / relative
        pairs.append((str(orig_guess), str(md_file)))

    output_path = out_root / output_filename
    aggregate_markdown_files(pairs, str(output_path), source_root=str(src_root))
    return str(output_path)
