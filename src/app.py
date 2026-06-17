import os
from pathlib import Path

from converter import convert_text_to_markdown
from folder_processor import list_text_files, read_file_content
from logger import setup_logger
from markdown_aggregator import aggregate_markdown_files


logger = setup_logger()


def main(source_folder: str, output_folder: str) -> str:
    os.makedirs(output_folder, exist_ok=True)

    text_files = list_text_files(source_folder)
    markdown_paths = []

    for text_file in text_files:
        content = read_file_content(text_file)
        markdown = convert_text_to_markdown(content)
        markdown_file = Path(output_folder) / (Path(text_file).stem + ".md")
        markdown_file.write_text(markdown, encoding="utf-8")
        markdown_paths.append(str(markdown_file))
        logger.info(f"Converted {text_file} -> {markdown_file}")

    aggregated_path = Path(output_folder) / "all_markdown.md"
    aggregate_markdown_files(markdown_paths, str(aggregated_path))
    logger.info(f"Aggregated markdown to {aggregated_path}")
    return str(aggregated_path)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python src/app.py <source_folder> <output_folder>")
        sys.exit(1)

    source = sys.argv[1]
    output = sys.argv[2]
    print(main(source, output))
