"""
prompt_generator.py — Tạo file _prompt.md gợi ý câu hỏi AI
cho hồ sơ thanh tra vừa chuyển đổi.

Mục tiêu: giúp cán bộ thanh tra biết cách tận dụng AI
(ChatGPT / Claude / NotebookLM) với tài liệu đã upload.
"""

from pathlib import Path
from datetime import datetime


# ─── Template prompt ────────────────────────────────────────────────────────

_TEMPLATE = """\
# Hướng dẫn sử dụng AI với hồ sơ thanh tra

> Sinh tự động bởi ThanhTra-MarkItDown {version} — {date}
> Thư mục hồ sơ: `{folder_name}`
> Số lượng tài liệu đã chuyển đổi: **{doc_count}** file

---

## 1. Cách nạp tài liệu vào AI

### ChatGPT / Claude
1. Mở file `_tong_hop.md` (hoặc từng file `.md` riêng lẻ)
2. Copy toàn bộ nội dung → paste vào hộp chat
3. Hoặc đính kèm file `.md` trực tiếp (Claude, GPT-4 hỗ trợ upload file)

### NotebookLM (Google)
1. Tạo Notebook mới tại [notebooklm.google.com](https://notebooklm.google.com)
2. Nhấn **Add sources** → upload file `_tong_hop.md`
3. NotebookLM sẽ tự phân tích và tạo tóm tắt

---

## 2. Gợi ý câu hỏi theo nghiệp vụ thanh tra

### 📋 Tổng quan hồ sơ
```
Hãy tóm tắt nội dung toàn bộ hồ sơ thanh tra này.
Liệt kê các vấn đề chính được phát hiện.
```

```
Đây là hồ sơ thanh tra về lĩnh vực gì? Đối tượng thanh tra là ai?
Thời gian và phạm vi thanh tra?
```

### 🔍 Phân tích vi phạm
```
Liệt kê các vi phạm được phát hiện trong hồ sơ.
Mỗi vi phạm: mô tả hành vi, căn cứ pháp lý vi phạm, mức độ nghiêm trọng.
```

```
Có những sai phạm nào liên quan đến tài chính, ngân sách không?
Tổng số tiền sai phạm là bao nhiêu?
```

### 📌 Kiến nghị và kết luận
```
Trình bày các kiến nghị trong kết luận thanh tra theo từng nhóm:
1. Kiến nghị xử lý hành chính
2. Kiến nghị thu hồi tài sản, tiền
3. Kiến nghị chuyển cơ quan điều tra (nếu có)
```

```
Đơn vị được thanh tra đã khắc phục những vấn đề nào?
Những vấn đề nào chưa được khắc phục?
```

### 📊 So sánh và đánh giá
```
So sánh kết quả thanh tra lần này với [lần trước / quy định hiện hành].
Điểm nào cải thiện, điểm nào vẫn còn tồn tại?
```

```
Đánh giá mức độ tuân thủ pháp luật của đơn vị được thanh tra.
Xếp loại: Tốt / Khá / Trung bình / Yếu và lý do.
```

### ✍️ Soạn thảo văn bản
```
Dựa trên hồ sơ này, hãy soạn thảo thông báo kết luận thanh tra
gửi đơn vị được thanh tra. Văn phong hành chính, ngắn gọn, đầy đủ.
```

```
Tóm tắt hồ sơ này thành báo cáo 1 trang để trình lãnh đạo.
Bao gồm: mục tiêu thanh tra, kết quả chính, kiến nghị quan trọng nhất.
```

---

## 3. Mẹo sử dụng hiệu quả

- **Đặt câu hỏi cụ thể**: Thay vì "phân tích hồ sơ", hãy hỏi "liệt kê các vi phạm về quản lý đất đai"
- **Yêu cầu trích dẫn**: Thêm "trích dẫn đoạn văn bản liên quan" để AI nêu rõ nguồn
- **Chia nhỏ câu hỏi**: Hỏi từng vấn đề một thay vì hỏi tất cả cùng lúc
- **Kiểm tra lại**: AI có thể nhầm — luôn đối chiếu với tài liệu gốc trước khi sử dụng

---

*Được tạo bởi ThanhTra-MarkItDown | Thanh tra tỉnh Quảng Ninh*
"""


# ─── Hàm công khai ──────────────────────────────────────────────────────────

def generate_prompt_file(
    output_folder: str,
    doc_count: int,
    folder_name: str = "",
    version: str = "v1.1",
) -> str:
    """
    Tạo file _prompt.md trong output_folder.

    Args:
        output_folder: thư mục chứa file .md đã chuyển đổi.
        doc_count: số file đã chuyển thành công.
        folder_name: tên thư mục hồ sơ nguồn (để hiển thị).
        version: phiên bản app.

    Returns:
        Đường dẫn file _prompt.md vừa tạo.
    """
    content = _TEMPLATE.format(
        version=version,
        date=datetime.now().strftime("%d/%m/%Y %H:%M"),
        folder_name=folder_name or Path(output_folder).name,
        doc_count=doc_count,
    )

    out_path = Path(output_folder) / "_prompt.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")
    return str(out_path)
