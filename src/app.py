"""
app.py — Giao diện chính ThanhTra-MarkItDown
CustomTkinter, 2 tab: Chuyển file đơn lẻ / Chuyển thư mục hồ sơ

UX v1.1:
- Lưu/khôi phục đường dẫn lần trước (config.json)
- Nút "Mở thư mục output" sau khi hoàn tất
- Cảnh báo thư mục nguồn rỗng
- Thông báo rõ hơn khi file đang bị khóa (Word/Excel đang mở)
- SKIPPED hiển thị riêng với prefix ⏭
"""

import sys
import json
import os
import threading
import subprocess
from pathlib import Path
from datetime import datetime

import customtkinter as ctk
from tkinter import filedialog, messagebox

# ─── Root dir ───────────────────────────────────────────────────────────────

if getattr(sys, "frozen", False):
    ROOT_DIR = Path(sys.executable).parent
else:
    ROOT_DIR = Path(__file__).resolve().parent.parent
    if str(ROOT_DIR) not in sys.path:
        sys.path.insert(0, str(ROOT_DIR))

from src.converter import DocumentConverter, PdfScanError
from src.folder_processor import FolderProcessor
from src.logger import ConversionLogger
from src.markdown_aggregator import aggregate_markdown_files
from src.prompt_generator import generate_prompt_file

# ─── Config ─────────────────────────────────────────────────────────────────

CONFIG_PATH = ROOT_DIR / "config.json"

def load_config() -> dict:
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}

def save_config(data: dict):
    try:
        cfg = load_config()
        cfg.update(data)
        CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

# ─── Giao diện ──────────────────────────────────────────────────────────────

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

APP_TITLE = "ThanhTra-MarkItDown"
APP_WIDTH = 780
APP_HEIGHT = 580
VERSION   = "v1.1"

# ─── Helper ─────────────────────────────────────────────────────────────────

def _timestamp_suffix() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def _open_folder(path: str):
    """Mở thư mục bằng File Explorer (Windows)."""
    try:
        os.startfile(path)
    except Exception:
        subprocess.Popen(["explorer", path])

def _friendly_error(exc: Exception) -> str:
    """Chuyển exception thành thông báo thân thiện."""
    msg = str(exc)
    if isinstance(exc, PermissionError) or "Permission" in msg or "being used" in msg:
        return (
            f"Không thể đọc file — file đang bị mở bởi ứng dụng khác\n"
            f"(Word/Excel/Acrobat đang mở). Hãy đóng ứng dụng rồi thử lại."
        )
    if isinstance(exc, PdfScanError):
        return f"PDF scan — cần OCR (tính năng v2.0): {exc}"
    return msg

# ─── Tab 1: Chuyển file đơn lẻ ──────────────────────────────────────────────

class SingleFileTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="transparent")
        self._last_output_dir: str = ""
        self._build_ui()
        self._restore_paths()

    def _build_ui(self):
        pad = {"padx": 16, "pady": 6}

        # File đầu vào
        ctk.CTkLabel(self, text="File đầu vào:", anchor="w").grid(
            row=0, column=0, sticky="w", **pad)
        self.input_var = ctk.StringVar()
        ctk.CTkEntry(self, textvariable=self.input_var, width=440).grid(
            row=0, column=1, sticky="ew", padx=(0, 6), pady=6)
        ctk.CTkButton(self, text="Chọn...", width=90,
                      command=self._pick_input).grid(row=0, column=2, pady=6, padx=(0, 16))

        # File đầu ra
        ctk.CTkLabel(self, text="File đầu ra (.md):", anchor="w").grid(
            row=1, column=0, sticky="w", **pad)
        self.output_var = ctk.StringVar()
        ctk.CTkEntry(self, textvariable=self.output_var, width=440).grid(
            row=1, column=1, sticky="ew", padx=(0, 6), pady=6)
        ctk.CTkButton(self, text="Chọn...", width=90,
                      command=self._pick_output).grid(row=1, column=2, pady=6, padx=(0, 16))

        # Nút chuyển đổi
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.grid(row=2, column=0, columnspan=3, pady=(12, 4), padx=16, sticky="w")
        self.btn_convert = ctk.CTkButton(
            btn_row, text="⚙  Chuyển đổi", command=self._convert, height=36, width=160)
        self.btn_convert.pack(side="left", padx=(0, 10))
        self.btn_open = ctk.CTkButton(
            btn_row, text="📂  Mở thư mục output", command=self._open_output,
            height=36, width=180, fg_color="gray40", hover_color="gray30")
        self.btn_open.pack(side="left")
        self.btn_open.configure(state="disabled")

        # Progress
        self.progress = ctk.CTkProgressBar(self)
        self.progress.set(0)
        self.progress.grid(row=3, column=0, columnspan=3, pady=(2, 2), padx=16, sticky="ew")

        # Log
        self.log_box = ctk.CTkTextbox(self, height=220, state="disabled", wrap="word")
        self.log_box.grid(row=4, column=0, columnspan=3, sticky="nsew", padx=16, pady=(4, 10))

        self.columnconfigure(1, weight=1)
        self.rowconfigure(4, weight=1)

    def _restore_paths(self):
        cfg = load_config()
        if cfg.get("single_input"):
            self.input_var.set(cfg["single_input"])
        if cfg.get("single_output"):
            self.output_var.set(cfg["single_output"])

    def _pick_input(self):
        cfg = load_config()
        init = cfg.get("single_input", "")
        init_dir = str(Path(init).parent) if init else ""
        exts = [
            ("Tài liệu hỗ trợ", "*.pdf *.docx *.xlsx *.xls *.pptx *.txt *.html *.htm"),
            ("Tất cả file", "*.*"),
        ]
        path = filedialog.askopenfilename(
            title="Chọn file cần chuyển", filetypes=exts, initialdir=init_dir)
        if path:
            self.input_var.set(path)
            self.output_var.set(str(Path(path).with_suffix(".md")))

    def _pick_output(self):
        path = filedialog.asksaveasfilename(
            title="Lưu file Markdown",
            defaultextension=".md",
            filetypes=[("Markdown", "*.md")],
        )
        if path:
            self.output_var.set(path)

    def _open_output(self):
        if self._last_output_dir:
            _open_folder(self._last_output_dir)
            self.after(300, self.winfo_toplevel().lift)

    def _log(self, msg: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _enable_open_btn(self):
        self.btn_open.configure(state="normal", fg_color=("#3B8ED0", "#1F6AA5"),
                                hover_color=("#36719F", "#144870"))

    def _convert(self):
        inp = self.input_var.get().strip()
        out = self.output_var.get().strip()

        if not inp:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn file đầu vào.")
            return
        if not out:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn file đầu ra.")
            return
        if not Path(inp).is_file():
            messagebox.showerror("Không tìm thấy file", f"File không tồn tại:\n{inp}")
            return

        self.btn_convert.configure(state="disabled")
        self.btn_open.configure(state="disabled", fg_color="gray40", hover_color="gray30")
        self.progress.set(0.2)
        save_config({"single_input": inp, "single_output": out})

        def run():
            try:
                conv = DocumentConverter()
                self.after(0, self._log,
                    f"[{datetime.now():%H:%M:%S}] Đang chuyển: {Path(inp).name}")
                conv.convert_and_save(inp, out)
                self._last_output_dir = str(Path(out).parent)
                self.after(0, self.progress.set, 1.0)
                self.after(0, self._log, f"✅ Thành công → {out}")
                self.after(0, self._enable_open_btn)
            except PdfScanError:
                self.after(0, self._log,
                    f"⏭ Bỏ qua: PDF scan — cần OCR (tính năng v2.0)")
                self.after(0, self.progress.set, 0)
            except Exception as ex:
                self.after(0, self._log, f"❌ Lỗi: {_friendly_error(ex)}")
                self.after(0, self.progress.set, 0)
            finally:
                self.after(0, lambda: self.btn_convert.configure(state="normal"))

        threading.Thread(target=run, daemon=True).start()


# ─── Tab 2: Chuyển thư mục ──────────────────────────────────────────────────

class FolderTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="transparent")
        self._last_output_dir: str = ""
        self._build_ui()
        self._restore_paths()

    def _build_ui(self):
        pad = {"padx": 16, "pady": 6}

        # Thư mục nguồn
        ctk.CTkLabel(self, text="Thư mục nguồn:", anchor="w").grid(
            row=0, column=0, sticky="w", **pad)
        self.src_var = ctk.StringVar()
        ctk.CTkEntry(self, textvariable=self.src_var, width=420).grid(
            row=0, column=1, sticky="ew", padx=(0, 6), pady=6)
        ctk.CTkButton(self, text="Chọn...", width=90,
                      command=self._pick_src).grid(row=0, column=2, pady=6, padx=(0, 16))

        # Thư mục đầu ra
        ctk.CTkLabel(self, text="Thư mục đầu ra:", anchor="w").grid(
            row=1, column=0, sticky="w", **pad)
        self.dst_var = ctk.StringVar()
        ctk.CTkEntry(self, textvariable=self.dst_var, width=420).grid(
            row=1, column=1, sticky="ew", padx=(0, 6), pady=6)
        ctk.CTkButton(self, text="Chọn...", width=90,
                      command=self._pick_dst).grid(row=1, column=2, pady=6, padx=(0, 16))

        # Tùy chọn
        opt_frame = ctk.CTkFrame(self, fg_color="transparent")
        opt_frame.grid(row=2, column=0, columnspan=3, sticky="w", padx=16, pady=(2, 2))
        self.opt_aggregate = ctk.CTkCheckBox(
            opt_frame, text="Sinh file tổng hợp (_tong_hop.md)")
        self.opt_aggregate.select()
        self.opt_aggregate.pack(side="left", padx=(0, 20))
        self.opt_log = ctk.CTkCheckBox(opt_frame, text="Ghi log")
        self.opt_log.select()
        self.opt_log.pack(side="left", padx=(0, 20))
        self.opt_prompt = ctk.CTkCheckBox(opt_frame, text="Sinh file gợi ý AI (_prompt.md)")
        self.opt_prompt.select()
        self.opt_prompt.pack(side="left", padx=(0, 20))

        # OCR row
        opt_frame2 = ctk.CTkFrame(self, fg_color="transparent")
        opt_frame2.grid(row=3, column=0, columnspan=3, sticky="w", padx=16, pady=(0, 2))
        self.opt_ocr = ctk.CTkCheckBox(
            opt_frame2,
            text="OCR cho PDF scan  (cần Tesseract — cài tại github.com/UB-Mannheim/tesseract)")
        self.opt_ocr.pack(side="left")

        # Progress
        self.progress = ctk.CTkProgressBar(self)
        self.progress.set(0)
        self.progress.grid(row=4, column=0, columnspan=3, pady=(6, 2), padx=16, sticky="ew")
        self.progress_label = ctk.CTkLabel(self, text="", anchor="w")
        self.progress_label.grid(row=5, column=0, columnspan=3, sticky="w", padx=16)

        # Nút bấm
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.grid(row=6, column=0, columnspan=3, pady=(6, 4), padx=16, sticky="w")
        self.btn_convert = ctk.CTkButton(
            btn_row, text="⚙  Bắt đầu chuyển đổi",
            command=self._start, height=36, width=200)
        self.btn_convert.pack(side="left", padx=(0, 10))
        self.btn_open = ctk.CTkButton(
            btn_row, text="📂  Mở thư mục output", command=self._open_output,
            height=36, width=180, fg_color="gray40", hover_color="gray30")
        self.btn_open.pack(side="left")
        self.btn_open.configure(state="disabled")

        # Log
        self.log_box = ctk.CTkTextbox(self, height=180, state="disabled", wrap="word")
        self.log_box.grid(row=7, column=0, columnspan=3, sticky="nsew", padx=16, pady=(4, 10))

        self.columnconfigure(1, weight=1)
        self.rowconfigure(7, weight=1)

    def _restore_paths(self):
        cfg = load_config()
        if cfg.get("folder_src"):
            self.src_var.set(cfg["folder_src"])
        if cfg.get("folder_dst"):
            self.dst_var.set(cfg["folder_dst"])

    def _pick_src(self):
        cfg = load_config()
        init = cfg.get("folder_src", "")
        path = filedialog.askdirectory(
            title="Chọn thư mục hồ sơ nguồn",
            initialdir=init or None)
        if path:
            self.src_var.set(path)
            p = Path(path)
            suggested = str(p.parent / f"{p.name}_MD_{_timestamp_suffix()}")
            self.dst_var.set(suggested)

    def _pick_dst(self):
        path = filedialog.askdirectory(title="Chọn thư mục lưu Markdown")
        if path:
            self.dst_var.set(path)

    def _open_output(self):
        if self._last_output_dir:
            _open_folder(self._last_output_dir)
            self.after(300, self.winfo_toplevel().lift)

    def _log(self, msg: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _enable_open_btn(self):
        self.btn_open.configure(state="normal", fg_color=("#3B8ED0", "#1F6AA5"),
                                hover_color=("#36719F", "#144870"))

    def _update_progress(self, current: int, total: int, filename: str):
        self.progress.set(current / total if total else 0)
        self.progress_label.configure(text=f"{current}/{total}  {filename}")

    def _start(self):
        src = self.src_var.get().strip()
        dst = self.dst_var.get().strip()

        if not src:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn thư mục nguồn.")
            return
        if not dst:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn thư mục đầu ra.")
            return
        if not Path(src).is_dir():
            messagebox.showerror("Không tìm thấy", f"Thư mục không tồn tại:\n{src}")
            return

        # Kiểm tra thư mục rỗng (không có file nào được hỗ trợ)
        conv_check = DocumentConverter()
        supported = [
            f for f in Path(src).rglob("*")
            if f.is_file() and conv_check.is_supported(str(f))
        ]
        if not supported:
            messagebox.showwarning(
                "Không có file hỗ trợ",
                f"Thư mục không chứa file nào được hỗ trợ.\n\n"
                f"Định dạng hỗ trợ: PDF, DOCX, XLSX, PPTX, TXT, HTML"
            )
            return

        self.btn_convert.configure(state="disabled")
        self.btn_open.configure(state="disabled")
        self.progress.set(0)
        self.progress_label.configure(text="Đang chuẩn bị…")

        do_log       = bool(self.opt_log.get())
        do_aggregate = bool(self.opt_aggregate.get())
        do_prompt    = bool(self.opt_prompt.get())
        do_ocr       = bool(self.opt_ocr.get())

        save_config({"folder_src": src, "folder_dst": dst})

        def on_progress(current, total, filename):
            self.after(0, self._update_progress, current, total, filename)

        def run():
            try:
                log_path = str(Path(dst) / "_conversion.log")
                logger   = ConversionLogger(log_path)
                processor = FolderProcessor(logger=logger, progress_callback=on_progress,
                                            use_ocr=do_ocr)

                self.after(0, self._log,
                    f"[{datetime.now():%H:%M:%S}] Bắt đầu xử lý: {src}")
                stats = processor.convert_folder(src, dst)

                # File tổng hợp
                if do_aggregate and stats["converted_pairs"]:
                    agg_path = str(Path(dst) / "_tong_hop.md")
                    pairs = [(str(s), str(m)) for s, m in stats["converted_pairs"]]
                    aggregate_markdown_files(pairs, agg_path, source_root=src)
                    self.after(0, self._log, f"📄 File tổng hợp: {agg_path}")

                # SKIPPED list
                if stats["skipped"] > 0:
                    self.after(0, self._log,
                        f"⏭ {stats['skipped']} file PDF scan bị bỏ qua "
                        f"(cần OCR — tính năng v2.0). Xem log để biết tên file.")

                self._last_output_dir = dst
                summary_text = (
                    f"Hoàn tất  ✓{stats['success']}  "
                    f"⏭{stats['skipped']}  ✗{stats['failed']}"
                )
                self.after(0, self.progress.set, 1.0)
                self.after(0, lambda t=summary_text: self.progress_label.configure(text=t))
                self.after(0, self._log,
                    f"✅ Hoàn tất — Tổng: {stats['total']} | "
                    f"Thành công: {stats['success']} | "
                    f"Bỏ qua: {stats['skipped']} | "
                    f"Lỗi: {stats['failed']}"
                )
                if do_prompt and stats["success"] > 0:
                    prompt_path = generate_prompt_file(
                        dst,
                        doc_count=stats["success"],
                        folder_name=Path(src).name,
                        version=VERSION,
                    )
                    self.after(0, self._log, f"💡 Gợi ý AI: {prompt_path}")
                if do_log:
                    self.after(0, self._log, f"📋 Log: {log_path}")
                self.after(0, self._enable_open_btn)

            except Exception as ex:
                self.after(0, self._log, f"❌ Lỗi nghiêm trọng: {_friendly_error(ex)}")
                self.after(0, self.progress.set, 0)
            finally:
                self.after(0, lambda: self.btn_convert.configure(state="normal"))

        threading.Thread(target=run, daemon=True).start()


# ─── Cửa sổ chính ───────────────────────────────────────────────────────────

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_TITLE} {VERSION}")
        self.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
        self.minsize(700, 480)
        self._build_ui()

    def _build_ui(self):
        header = ctk.CTkFrame(self, corner_radius=0, height=46)
        header.pack(fill="x", side="top")
        ctk.CTkLabel(
            header,
            text=f"  {APP_TITLE}  –  Chuyển hồ sơ thanh tra sang Markdown",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(side="left", padx=12, pady=10)
        ctk.CTkLabel(
            header, text=VERSION, font=ctk.CTkFont(size=11), text_color="gray"
        ).pack(side="right", padx=12)

        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=(6, 10))

        tab1 = self.tabs.add("📄  Chuyển file")
        tab2 = self.tabs.add("📂  Chuyển thư mục")

        SingleFileTab(tab1).pack(fill="both", expand=True)
        FolderTab(tab2).pack(fill="both", expand=True)

        self.tabs.set("📂  Chuyển thư mục")


# ─── Entry point ─────────────────────────────────────────────────────────────

def main():
    App().mainloop()

if __name__ == "__main__":
    main()
