# ThanhTra-MarkItDown

Công cụ Windows hỗ trợ cán bộ thanh tra chuyển đổi hồ sơ (PDF, DOCX, XLSX, PPTX, TXT, HTML) sang Markdown để đưa vào ChatGPT, NotebookLM, Claude và các AI khác.

## Tính năng (v1)

- **Chuyển file đơn lẻ**: PDF có text, DOCX, XLSX, PPTX, TXT, HTML
- **Chuyển cả thư mục**: đệ quy, giữ nguyên cấu trúc thư mục con
- **Sinh file tổng hợp** `_tong_hop.md` dùng upload NotebookLM / ChatGPT
- **Ghi log** với timestamp (SUCCESS / ERROR)
- **Giao diện GUI** CustomTkinter, progress bar, 2 tab

## Cài đặt và chạy (development)

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

python src\app.py
```

## Chạy tests

```bat
.venv\Scripts\activate
python -m pytest tests\ -v
```

## Build EXE

```bat
build_exe.bat
```

File output: `dist\ThanhTra-MarkItDown.exe`

## Cấu trúc project

```
ThanhTra-MarkItDown/
├── src/
│   ├── app.py                  # GUI (CustomTkinter)
│   ├── converter.py            # DocumentConverter (MarkItDown)
│   ├── folder_processor.py     # Xử lý thư mục đệ quy
│   ├── markdown_aggregator.py  # Gộp nhiều .md thành 1 file
│   └── logger.py               # ConversionLogger
├── tests/
│   ├── test_converter.py
│   └── test_folder_processor.py
├── sample_data/
│   └── KL30/                   # Dữ liệu mẫu thư mục hồ sơ
├── output/                     # Kết quả chuyển đổi
├── assets/
│   └── icon.ico
├── conftest.py                 # pytest path config
├── requirements.txt
└── build_exe.bat
```

## Định dạng file tổng hợp

```markdown
# Tài liệu: BaoCao.docx

Nguồn:
BaoCao.docx

---

(nội dung markdown)

==================================================

# Tài liệu: KetLuan.pdf
...
```

## Công nghệ

- Python 3.12
- [MarkItDown](https://github.com/microsoft/markitdown) (Microsoft)
- CustomTkinter
- PyMuPDF
- PyInstaller
