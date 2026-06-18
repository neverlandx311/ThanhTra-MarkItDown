"""
app.py — Giao diện chính ThanhTra-MarkItDown
CustomTkinter, 2 tab: Chuyển file đơn lẻ / Chuyển thư mục hồ sơ
"""

import sys
import threading
from pathlib import Path
from datetime import datetime

import customtkinter as ctk
from tkinter import filedialog, messagebox

# Xác định thư mục gốc — hoạt động cả khi chạy .py lẫn EXE (PyInstaller)
if getattr(sys, "frozen", False):
    # Đang chạy dưới dạng EXE → ROOT_DIR là thư mục chứa file .exe
    ROOT_DIR = Path(sys.executable).parent
else:
    ROOT_DIR = Path(__file__).resolve().parent.parent
    if str(ROOT_DIR) not in sys.path:
        sys.path.insert(0, str(ROOT_DIR))

from src.converter import DocumentConverter
from src.folder_processor import FolderProcessor
from src.logger import ConversionLogger
from src.markdown_aggregator import aggregate_markdown_files


# ─── Cấu hình giao diện ─────────────────────────────────────────────────────

ctk.set_appearance_mode("System")          # System / Light / Dark
ctk.set_default_color_theme("blue")

APP_TITLE  = "ThanhTra-MarkItDown"
APP_WIDTH  = 760
APP_HEIGHT = 540
VERSION    = "v1.0"


# ─── Helper ─────────────────────────────────────────────────────────────────

def _default_log_path() -> str:
    return str(ROOT_DIR / "output" / "conversion.log")


def _timestamp_folder(base: str) -> str:
    """output/KL30_MD_20240618_143022"""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base}_{ts}"


# ─── Tab 1: Chuyển file đơn lẻ ──────────────────────────────────────────────

class SingleFileTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="transparent")
        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 16, "pady": 6}

        # --- Chọn file đầu vào ---
        ctk.CTkLabel(self, text="File đầu vào:", anchor="w").grid(
            row=0, column=0, sticky="w", **pad
        )
        self.input_var = ctk.StringVar()
        ctk.CTkEntry(self, textvariable=self.input_var, width=460).grid(
            row=0, column=1, sticky="ew", padx=(0, 6), pady=6
        )
        ctk.CTkButton(self, text="Chọn...", width=90,
                      command=self._pick_input).grid(row=0, column=2, pady=6, padx=(0, 16))

        # --- File đầu ra ---
        ctk.CTkLabel(self, text="File đầu ra (.md):", anchor="w").grid(
            row=1, column=0, sticky="w", **pad
        )
        self.output_var = ctk.StringVar()
        ctk.CTkEntry(self, textvariable=self.output_var, width=460).grid(
            row=1, column=1, sticky="ew", padx=(0, 6), pady=6
        )
        ctk.CTkButton(self, text="Chọn...", width=90,
                      command=self._pick_output).grid(row=1, column=2, pady=6, padx=(0, 16))

        # --- Nút chuyển đổi ---
        self.btn_convert = ctk.CTkButton(
            self, text="⚙  Chuyển đổi", command=self._convert, height=38
        )
        self.btn_convert.grid(row=2, column=0, columnspan=3, pady=(14, 6), padx=16)

        # --- Progress bar ---
        self.progress = ctk.CTkProgressBar(self, width=560)
        self.progress.set(0)
        self.progress.grid(row=3, column=0, columnspan=3, pady=4, padx=16, sticky="ew")

        # --- Log box ---
        self.log_box = ctk.CTkTextbox(self, height=200, state="disabled", wrap="word")
        self.log_box.grid(row=4, column=0, columnspan=3, sticky="nsew", padx=16, pady=(6, 10))

        self.columnconfigure(1, weight=1)
        self.rowconfigure(4, weight=1)

    # --- Callbacks ---

    def _pick_input(self):
        exts = [
            ("Tài liệu hỗ trợ", "*.pdf *.docx *.xlsx *.xls *.pptx *.txt *.html *.htm"),
            ("Tất cả file", "*.*"),
        ]
        path = filedialog.askopenfilename(title="Chọn file cần chuyển", filetypes=exts)
        if path:
            self.input_var.set(path)
            # Tự đề xuất file output
            p = Path(path)
            self.output_var.set(str(p.with_suffix(".md")))

    def _pick_output(self):
        path = filedialog.asksaveasfilename(
            title="Lưu file Markdown",
            defaultextension=".md",
            filetypes=[("Markdown", "*.md")],
        )
        if path:
            self.output_var.set(path)

    def _log(self, msg: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _convert(self):
        inp = self.input_var.get().strip()
        out = self.output_var.get().strip()

        if not inp:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn file đầu vào.")
            return
        if not out:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn file đầu ra.")
            return

        self.btn_convert.configure(state="disabled")
        self.progress.set(0.2)

        def run():
            try:
                conv = DocumentConverter()
                self._log(f"[{datetime.now():%H:%M:%S}] Đang chuyển: {Path(inp).name}")
                conv.convert_and_save(inp, out)
                self.after(0, self.progress.set, 1.0)
                self.after(0, self._log, f"✅ Thành công → {out}")
            except Exception as ex:
                self.after(0, self._log, f"❌ Lỗi: {ex}")
                self.after(0, self.progress.set, 0)
            finally:
                self.after(0, self.btn_convert.configure, {"state": "normal"})

        threading.Thread(target=run, daemon=True).start()


# ─── Tab 2: Chuyển thư mục ──────────────────────────────────────────────────

class FolderTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="transparent")
        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 16, "pady": 6}

        # --- Thư mục nguồn ---
        ctk.CTkLabel(self, text="Thư mục nguồn:", anchor="w").grid(
            row=0, column=0, sticky="w", **pad
        )
        self.src_var = ctk.StringVar()
        ctk.CTkEntry(self, textvariable=self.src_var, width=440).grid(
            row=0, column=1, sticky="ew", padx=(0, 6), pady=6
        )
        ctk.CTkButton(self, text="Chọn...", width=90,
                      command=self._pick_src).grid(row=0, column=2, pady=6, padx=(0, 16))

        # --- Thư mục đầu ra ---
        ctk.CTkLabel(self, text="Thư mục đầu ra:", anchor="w").grid(
            row=1, column=0, sticky="w", **pad
        )
        self.dst_var = ctk.StringVar()
        ctk.CTkEntry(self, textvariable=self.dst_var, width=440).grid(
            row=1, column=1, sticky="ew", padx=(0, 6), pady=6
        )
        ctk.CTkButton(self, text="Chọn...", width=90,
                      command=self._pick_dst).grid(row=1, column=2, pady=6, padx=(0, 16))

        # --- Tùy chọn ---
        opt_frame = ctk.CTkFrame(self, fg_color="transparent")
        opt_frame.grid(row=2, column=0, columnspan=3, sticky="w", padx=16, pady=(4, 2))

        self.opt_keep_structure = ctk.CTkCheckBox(opt_frame, text="Giữ cấu trúc thư mục")
        self.opt_keep_structure.select()
        self.opt_keep_structure.pack(side="left", padx=(0, 20))

        self.opt_aggregate = ctk.CTkCheckBox(opt_frame, text="Sinh file tổng hợp (_tong_hop.md)")
        self.opt_aggregate.select()
        self.opt_aggregate.pack(side="left", padx=(0, 20))

        self.opt_log = ctk.CTkCheckBox(opt_frame, text="Ghi log")
        self.opt_log.select()
        self.opt_log.pack(side="left")

        # --- Progress bar + nhãn ---
        self.progress = ctk.CTkProgressBar(self, width=560)
        self.progress.set(0)
        self.progress.grid(row=3, column=0, columnspan=3, pady=(8, 2), padx=16, sticky="ew")

        self.progress_label = ctk.CTkLabel(self, text="", anchor="w")
        self.progress_label.grid(row=4, column=0, columnspan=3, sticky="w", padx=16)

        # --- Nút bấm ---
        self.btn_convert = ctk.CTkButton(
            self, text="⚙  Bắt đầu chuyển đổi", command=self._start, height=38
        )
        self.btn_convert.grid(row=5, column=0, columnspan=3, pady=(8, 4), padx=16)

        # --- Log box ---
        self.log_box = ctk.CTkTextbox(self, height=180, state="disabled", wrap="word")
        self.log_box.grid(row=6, column=0, columnspan=3, sticky="nsew", padx=16, pady=(4, 10))

        self.columnconfigure(1, weight=1)
        self.rowconfigure(6, weight=1)

    # --- Callbacks ---

    def _pick_src(self):
        path = filedialog.askdirectory(title="Chọn thư mục hồ sơ nguồn")
        if path:
            self.src_var.set(path)
            # Đề xuất thư mục output cạnh thư mục nguồn
            p = Path(path)
            self.dst_var.set(str(p.parent / _timestamp_folder(p.name + "_MD")))

    def _pick_dst(self):
        path = filedialog.askdirectory(title="Chọn thư mục lưu Markdown")
        if path:
            self.dst_var.set(path)

    def _log(self, msg: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _update_progress(self, current: int, total: int, filename: str):
        if total:
            self.progress.set(current / total)
        self.progress_label.configure(
            text=f"{current}/{total}  {filename}"
        )

    def _start(self):
        src = self.src_var.get().strip()
        dst = self.dst_var.get().strip()

        if not src:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn thư mục nguồn.")
            return
        if not dst:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn thư mục đầu ra.")
            return

        self.btn_convert.configure(state="disabled")
        self.progress.set(0)
        self.progress_label.configure(text="Đang chuẩn bị…")

        do_log       = self.opt_log.get()
        do_aggregate = self.opt_aggregate.get()

        def on_progress(current, total, filename):
            self.after(0, self._update_progress, current, total, filename)

        def run():
            try:
                log_path = _default_log_path() if do_log else str(
                    Path(dst) / "_conversion.log"
                )
                logger = ConversionLogger(log_path)
                processor = FolderProcessor(
                    logger=logger,
                    progress_callback=on_progress,
                )

                self.after(0, self._log, f"[{datetime.now():%H:%M:%S}] Bắt đầu xử lý: {src}")
                stats = processor.convert_folder(src, dst)

                # Sinh file tổng hợp
                if do_aggregate and stats["converted_pairs"]:
                    agg_path = str(Path(dst) / "_tong_hop.md")
                    pairs = [
                        (str(Path(src_f)), str(md_f))
                        for src_f, md_f in stats["converted_pairs"]
                    ]
                    aggregate_markdown_files(pairs, agg_path, source_root=src)
                    self.after(0, self._log, f"📄 File tổng hợp: {agg_path}")

                self.after(0, self.progress.set, 1.0)
                self.after(0, self.progress_label.configure, {
                    "text": f"Hoàn tất: {stats['success']} thành công, {stats['failed']} lỗi"
                })
                self.after(0, self._log,
                    f"✅ Hoàn tất — Tổng: {stats['total']} | "
                    f"Thành công: {stats['success']} | "
                    f"Bỏ qua (PDF scan): {stats['skipped']} | "
                    f"Lỗi: {stats['failed']}"
                )
                if do_log:
                    self.after(0, self._log, f"📋 Log: {log_path}")

            except Exception as ex:
                self.after(0, self._log, f"❌ Lỗi nghiêm trọng: {ex}")
                self.after(0, self.progress.set, 0)
            finally:
                self.after(0, self.btn_convert.configure, {"state": "normal"})

        threading.Thread(target=run, daemon=True).start()


# ─── Cửa sổ chính ───────────────────────────────────────────────────────────

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_TITLE} {VERSION}")
        self.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
        self.minsize(680, 460)
        self._build_ui()

    def _build_ui(self):
        # Header
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

        # Tabs
        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=(6, 10))

        tab1 = self.tabs.add("📄  Chuyển file")
        tab2 = self.tabs.add("📂  Chuyển thư mục")

        SingleFileTab(tab1).pack(fill="both", expand=True)
        FolderTab(tab2).pack(fill="both", expand=True)

        # Mặc định mở tab 2 (hay dùng hơn)
        self.tabs.set("📂  Chuyển thư mục")


# ─── Entry point ─────────────────────────────────────────────────────────────

def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
