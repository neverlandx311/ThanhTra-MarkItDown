"""
conftest.py — đặt ở root project.
Tự động thêm thư mục gốc vào sys.path để pytest tìm được package src.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
