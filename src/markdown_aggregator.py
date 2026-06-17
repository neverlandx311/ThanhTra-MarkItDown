from pathlib import Path
from typing import List


def aggregate_markdown_files(paths: List[str], output_path: str) -> None:
    """Aggregate multiple Markdown files into a single output file."""
    aggregated_lines: List[str] = []

    for path in paths:
        file_path = Path(path)
        if not file_path.is_file():
            raise FileNotFoundError(f"Markdown file not found: {path}")

        aggregated_lines.append(f"<!-- Begin: {file_path.name} -->")
        aggregated_lines.extend(file_path.read_text(encoding="utf-8").splitlines())
        aggregated_lines.append(f"<!-- End: {file_path.name} -->")
        aggregated_lines.append("")

    Path(output_path).write_text("\n".join(aggregated_lines).strip() + "\n", encoding="utf-8")
