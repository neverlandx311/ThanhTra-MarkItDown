import os
from typing import List


def list_text_files(folder: str) -> List[str]:
    """Return a sorted list of text file paths in the given folder."""
    if not os.path.isdir(folder):
        raise FileNotFoundError(f"Folder not found: {folder}")

    files = [
        os.path.join(folder, entry)
        for entry in os.listdir(folder)
        if os.path.isfile(os.path.join(folder, entry)) and entry.lower().endswith(".txt")
    ]
    return sorted(files)


def read_file_content(path: str) -> str:
    """Read file content using UTF-8 encoding."""
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()
