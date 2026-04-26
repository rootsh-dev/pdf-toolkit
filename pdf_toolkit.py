#!/usr/bin/env python3
"""
PDF Toolkit - A full-featured offline PDF tool inspired by ilovepdf.com
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
import io
import sys
import threading
import shutil
import tempfile
from pathlib import Path

# ─── Colours & Fonts ────────────────────────────────────────────────────────
BG        = "#f5f6fa"
SIDEBAR   = "#1e1e2e"
ACCENT    = "#e84343"
CARD_BG   = "#ffffff"
TEXT_DARK = "#1a1a2e"
TEXT_GRAY = "#6c757d"
SUCCESS   = "#28a745"
BTN_HOVER = "#c0392b"
TOOL_COLORS = {
    "Merge PDF":       "#e84343",
    "Split PDF":       "#f39c12",
    "Compress PDF":    "#27ae60",
    "Rotate PDF":      "#8e44ad",
    "PDF to JPG":      "#2980b9",
    "JPG to PDF":      "#16a085",
    "Add Watermark":   "#d35400",
    "Page Numbers":    "#2c3e50",
    "Protect PDF":     "#c0392b",
    "Unlock PDF":      "#27ae60",
    "Organize Pages":  "#8e44ad",
    "Extract Text":    "#2980b9",
    "Extract Images":  "#16a085",
    "PDF to Word":     "#2454a4",
    "Word to PDF":     "#e84343",
    "Repair PDF":      "#f39c12",
    "PPT to PDF":      "#d04423",
}
TOOL_ICONS = {
    "Merge PDF":       "⊕",
    "Split PDF":       "✂",
    "Compress PDF":    "⇩",
    "Rotate PDF":      "↻",
    "PDF to JPG":      "🖼",
    "JPG to PDF":      "📄",
    "Add Watermark":   "◈",
    "Page Numbers":    "#",
    "Protect PDF":     "🔒",
    "Unlock PDF":      "🔓",
    "Organize Pages":  "⊞",
    "Extract Text":    "T",
    "Extract Images":  "⎙",
    "PDF to Word":     "W",
    "Word to PDF":     "P",
    "Repair PDF":      "⚙",
    "PPT to PDF":      "📊",
}


def run_in_thread(fn):
    t = threading.Thread(target=fn, daemon=True)
    t.start()


class StatusBar(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=SIDEBAR, height=30)
        self.lbl = tk.Label(self, text="Ready", bg=SIDEBAR, fg="#aaa",
                            font=("Segoe UI", 9))
        self.lbl.pack(side="left", padx=12)
        self.progress = ttk.Progressbar(self, length=200, mode="indeterminate")

    def set(self, msg, busy=False):
        self.lbl.config(text=msg)
        if busy:
            self.progress.pack(side="right", padx=12, pady=3)
            self.progress.start(10)
        else:
            self.progress.stop()
            self.progress.pack_forget()


class ToolCard(tk.Frame):
    def __init__(self, parent, name, command, col):
        super().__init__(parent, bg=CARD_BG, bd=0,
                         relief="flat", cursor="hand2",
                         width=160, height=120)
        self.pack_propagate(False)
        self.name = name
        self.command = command
        self.color = TOOL_COLORS.get(name, ACCENT)
        icon_text = TOOL_ICONS.get(name, "•")

        top = tk.Frame(self, bg=self.color, height=55)
        top.pack(fill="x")
        top.pack_propagate(False)
        tk.Label(top, text=icon_text, bg=self.color, fg="white",
                 font=("Segoe UI", 22)).pack(expand=True)

        tk.Label(self, text=name, bg=CARD_BG, fg=TEXT_DARK,
                 font=("Segoe UI", 9, "bold"),
                 wraplength=140, justify="center").pack(pady=8, padx=4)

        for w in (self, top, *self.winfo_children()):
            w.bind("<Button-1>", lambda e: command())
            w.bind("<Enter>", self._on_enter)
            w.bind("<Leave>", self._on_leave)

    def _on_enter(self, e):
        self.config(relief="groove", bd=1)

    def _on_leave(self, e):
        self.config(relief="flat", bd=0)


class FileDropZone(tk.Frame):
    def __init__(self, parent, label="Click or drag files here",
                 multiple=False, filetypes=None, **kw):
        super().__init__(parent, bg="#eef2ff", bd=2,
                         relief="solid", cursor="hand2", **kw)
        self.multiple  = multiple
        self.filetypes = filetypes or [("PDF files", "*.pdf")]
        self.files: list[str] = []

        self.lbl = tk.Label(self, text=f"📁  {label}", bg="#eef2ff",
                            fg=TEXT_GRAY, font=("Segoe UI", 11))
        self.lbl.pack(expand=True, pady=20)
        self.file_frame = tk.Frame(self, bg="#eef2ff")
        self.file_frame.pack(fill="x", padx=10)

        for w in (self, self.lbl):
            w.bind("<Button-1>", lambda e: self._pick())

    def _pick(self):
        if self.multiple:
            paths = filedialog.askopenfilenames(filetypes=self.filetypes)
            if paths:
                for p in paths:
                    if p not in self.files:
                        self.files.append(p)
        else:
            path = filedialog.askopenfilename(filetypes=self.filetypes)
            if path:
                self.files = [path]
        self._refresh()

    def _refresh(self):
        for w in self.file_frame.winfo_children():
            w.destroy()
        for i, f in enumerate(self.files):
            row = tk.Frame(self.file_frame, bg="#dde4ff")
            row.pack(fill="x", pady=1)
            
            btn_frame = tk.Frame(row, bg="#dde4ff")
            btn_frame.pack(side="right", padx=4)
            
            tk.Button(btn_frame, text="❌", bd=0, bg="#dde4ff", fg="#e84343", 
                      cursor="hand2", command=lambda idx=i: self._remove(idx)).pack(side="right", padx=2)
            if i < len(self.files) - 1:
                tk.Button(btn_frame, text="↓", bd=0, bg="#dde4ff", fg="#333", 
                          cursor="hand2", command=lambda idx=i: self._move(idx, 1)).pack(side="right", padx=2)
            if i > 0:
                tk.Button(btn_frame, text="↑", bd=0, bg="#dde4ff", fg="#333", 
                          cursor="hand2", command=lambda idx=i: self._move(idx, -1)).pack(side="right", padx=2)
            
            tk.Label(row, text="📄 " + os.path.basename(f),
                     bg="#dde4ff", fg=TEXT_DARK,
                     font=("Segoe UI", 9), anchor="w").pack(side="left",
                                                             padx=6, pady=2)
        n = len(self.files)
        msg = f"✔  {n} file{'s' if n>1 else ''} selected  (click to add more)" if self.multiple else f"✔  {n} file selected  (click to change)"
        self.lbl.config(text=msg)

    def _remove(self, idx):
        self.files.pop(idx)
        self._refresh()

    def _move(self, idx, dir):
        new_idx = idx + dir
        if 0 <= new_idx < len(self.files):
            self.files[idx], self.files[new_idx] = self.files[new_idx], self.files[idx]
            self._refresh()

    def clear(self):
        self.files = []
        self.lbl.config(text="📁  Click or drag files here")
        for w in self.file_frame.winfo_children():
            w.destroy()


def action_btn(parent, text, command, color=ACCENT):
    btn = tk.Button(parent, text=text, command=command,
                    bg=color, fg="white",
                    font=("Segoe UI", 11, "bold"),
                    relief="flat", cursor="hand2",
                    padx=22, pady=10, bd=0)
    btn.bind("<Enter>", lambda e: btn.config(bg=BTN_HOVER))
    btn.bind("<Leave>", lambda e: btn.config(bg=color))
    return btn


def labeled(parent, text):
    tk.Label(parent, text=text, bg=BG, fg=TEXT_DARK,
             font=("Segoe UI", 10)).pack(anchor="w", pady=(8, 2))


# ════════════════════════════════════════════════════════════════════════════
# Tool Views
# ════════════════════════════════════════════════════════════════════════════

class BaseToolView(tk.Frame):
    def __init__(self, parent, app, title):
        super().__init__(parent, bg=BG)
        self.app = app
        tk.Button(self, text="← Back", command=app.show_home,
                  bg=BG, fg=TEXT_GRAY, relief="flat",
                  font=("Segoe UI", 10), cursor="hand2").pack(anchor="w", padx=20, pady=(15, 0))
        tk.Label(self, text=title, bg=BG, fg=TEXT_DARK,
                 font=("Segoe UI", 18, "bold")).pack(pady=(4, 16), padx=20, anchor="w")
        self.body = tk.Frame(self, bg=BG)
        self.body.pack(fill="both", expand=True, padx=28)


# ── 1. Merge PDF ─────────────────────────────────────────────────────────────
class MergeView(BaseToolView):
    def __init__(self, p, app):
        super().__init__(p, app, "Merge PDF")
        self.zone = FileDropZone(self.body, "Select PDF files to merge",
                                 multiple=True, height=120)
        self.zone.pack(fill="x", pady=4)
        action_btn(self.body, "Merge PDFs", self._run).pack(pady=12)

    def _run(self):
        if not self.zone.files:
            return messagebox.showwarning("No files", "Please select PDF files.")
        out = filedialog.asksaveasfilename(defaultextension=".pdf",
                                           filetypes=[("PDF", "*.pdf")],
                                           initialfile="merged.pdf")
        if not out: return
        self.app.status.set("Merging…", busy=True)
        def work():
            try:
                from pypdf import PdfWriter, PdfReader
                w = PdfWriter()
                for f in self.zone.files:
                    r = PdfReader(f)
                    for pg in r.pages:
                        w.add_page(pg)
                with open(out, "wb") as fh:
                    w.write(fh)
                self.app.after(0, lambda: (self.app.status.set("✔ Merged successfully!"),
                                           messagebox.showinfo("Done", f"Saved:\n{out}")))
            except Exception as e:
                err_msg = str(e)
                self.app.after(0, lambda err=err_msg: (self.app.status.set("Error"),
                                           messagebox.showerror("Error", err)))
        run_in_thread(work)


# ── 2. Split PDF ─────────────────────────────────────────────────────────────
class SplitView(BaseToolView):
    def __init__(self, p, app):
        super().__init__(p, app, "Split PDF")
        self.zone = FileDropZone(self.body, "Select a PDF to split", height=120)
        self.zone.pack(fill="x", pady=4)

        rf = tk.Frame(self.body, bg=BG)
        rf.pack(fill="x", pady=4)
        tk.Label(rf, text="Split mode:", bg=BG, fg=TEXT_DARK,
                 font=("Segoe UI", 10)).pack(side="left")
        self.mode = tk.StringVar(value="all")
        ttk.Combobox(rf, textvariable=self.mode,
                     values=["all", "range", "every_n"],
                     state="readonly", width=14).pack(side="left", padx=8)

        labeled(self.body, "Range (e.g. 1-3,5) or N (for every_n):")
        self.rng = tk.Entry(self.body, font=("Segoe UI", 10), relief="solid", bd=1)
        self.rng.pack(fill="x", pady=2)

        action_btn(self.body, "Split PDF", self._run, color="#f39c12").pack(pady=12)

    def _run(self):
        if not self.zone.files:
            return messagebox.showwarning("No file", "Select a PDF first.")
        out_dir = filedialog.askdirectory(title="Choose output folder")
        if not out_dir: return
        src = self.zone.files[0]
        mode = self.mode.get()
        rng  = self.rng.get().strip()
        self.app.status.set("Splitting…", busy=True)

        def work():
            try:
                from pypdf import PdfReader, PdfWriter
                reader = PdfReader(src)
                total  = len(reader.pages)
                base   = Path(src).stem

                def save_pages(indices, suffix):
                    w = PdfWriter()
                    for i in indices:
                        w.add_page(reader.pages[i])
                    path = os.path.join(out_dir, f"{base}_{suffix}.pdf")
                    with open(path, "wb") as fh:
                        w.write(fh)

                if mode == "all":
                    for i in range(total):
                        save_pages([i], f"page{i+1}")
                elif mode == "every_n":
                    n = int(rng) if rng.isdigit() else 1
                    for start in range(0, total, n):
                        chunk = list(range(start, min(start+n, total)))
                        save_pages(chunk, f"pages{start+1}-{chunk[-1]+1}")
                elif mode == "range":
                    indices = []
                    for part in rng.split(","):
                        part = part.strip()
                        if "-" in part:
                            a, b = part.split("-")
                            indices += list(range(int(a)-1, int(b)))
                        else:
                            indices.append(int(part)-1)
                    save_pages(indices, "range")
                self.app.after(0, lambda: (self.app.status.set("✔ Split done!"),
                                           messagebox.showinfo("Done", f"Files saved to:\n{out_dir}")))
            except Exception as e:
                err_msg = str(e)
                self.app.after(0, lambda err=err_msg: (self.app.status.set("Error"),
                                           messagebox.showerror("Error", err)))
        run_in_thread(work)


# ── 3. Compress PDF ──────────────────────────────────────────────────────────
class CompressView(BaseToolView):
    def __init__(self, p, app):
        super().__init__(p, app, "Compress PDF")
        self.zone = FileDropZone(self.body, "Select PDF to compress",
                                 multiple=True, height=120)
        self.zone.pack(fill="x", pady=4)
        labeled(self.body, "Image quality (1–95, lower = smaller file):")
        self.qual = tk.Scale(self.body, from_=10, to=95, orient="horizontal",
                             bg=BG, fg=TEXT_DARK, troughcolor="#ddd",
                             highlightthickness=0)
        self.qual.set(60)
        self.qual.pack(fill="x", pady=2)
        action_btn(self.body, "Compress", self._run, color="#27ae60").pack(pady=12)

    def _run(self):
        if not self.zone.files:
            return messagebox.showwarning("No files", "Select PDF files first.")
        out_dir = filedialog.askdirectory(title="Output folder")
        if not out_dir: return
        q = self.qual.get()
        self.app.status.set("Compressing…", busy=True)

        def work():
            try:
                saved_total = 0
                for f in self.zone.files:
                    orig = os.path.getsize(f)
                    out_path = os.path.join(out_dir, "compressed_" + os.path.basename(f))
                    
                    _compress_pdf_smart(f, out_path, q)
                    
                    if os.path.exists(out_path):
                        new = os.path.getsize(out_path)
                        if new < orig:
                            saved_total += orig - new
                        else:
                            import shutil
                            shutil.copy2(f, out_path)
                            
                msg = f"Done! Saved approx {saved_total//1024} KB total.\nFiles in:\n{out_dir}"
                self.app.after(0, lambda: (self.app.status.set("✔ Compressed!"),
                                           messagebox.showinfo("Done", msg)))
            except Exception as e:
                err_msg = str(e)
                self.app.after(0, lambda err=err_msg: (self.app.status.set("Error"),
                                           messagebox.showerror("Error", err)))
        run_in_thread(work)


# ── 4. Rotate PDF ────────────────────────────────────────────────────────────
class RotateView(BaseToolView):
    def __init__(self, p, app):
        super().__init__(p, app, "Rotate PDF")
        self.zone = FileDropZone(self.body, "Select PDF to rotate",
                                 multiple=True, height=120)
        self.zone.pack(fill="x", pady=4)
        rf = tk.Frame(self.body, bg=BG)
        rf.pack(fill="x", pady=4)
        tk.Label(rf, text="Rotation:", bg=BG, fg=TEXT_DARK,
                 font=("Segoe UI", 10)).pack(side="left")
        self.rot = tk.StringVar(value="90")
        for v, lbl in [("90","90° CW"), ("180","180°"), ("270","90° CCW")]:
            tk.Radiobutton(rf, text=lbl, variable=self.rot, value=v,
                           bg=BG, font=("Segoe UI", 10)).pack(side="left", padx=8)

        labeled(self.body, "Apply to pages (e.g. all / 1,3,5 / 1-4):")
        self.pages_entry = tk.Entry(self.body, font=("Segoe UI", 10),
                                    relief="solid", bd=1)
        self.pages_entry.insert(0, "all")
        self.pages_entry.pack(fill="x", pady=2)

        action_btn(self.body, "Rotate", self._run, color="#8e44ad").pack(pady=12)

    def _run(self):
        if not self.zone.files:
            return messagebox.showwarning("No files", "Select PDF files first.")
        out_dir = filedialog.askdirectory(title="Output folder")
        if not out_dir: return
        deg = int(self.rot.get())
        pg_str = self.pages_entry.get().strip()
        self.app.status.set("Rotating…", busy=True)

        def work():
            try:
                from pypdf import PdfReader, PdfWriter
                for f in self.zone.files:
                    reader = PdfReader(f)
                    total  = len(reader.pages)
                    if pg_str.lower() == "all":
                        targets = set(range(total))
                    else:
                        targets = set()
                        for part in pg_str.split(","):
                            part = part.strip()
                            if "-" in part:
                                a, b = part.split("-")
                                targets |= set(range(int(a)-1, int(b)))
                            else:
                                targets.add(int(part)-1)
                    writer = PdfWriter()
                    for i, pg in enumerate(reader.pages):
                        if i in targets:
                            pg.rotate(deg)
                        writer.add_page(pg)
                    out = os.path.join(out_dir, "rotated_" + os.path.basename(f))
                    with open(out, "wb") as fh:
                        writer.write(fh)
                self.app.after(0, lambda: (self.app.status.set("✔ Rotated!"),
                                           messagebox.showinfo("Done", f"Saved to:\n{out_dir}")))
            except Exception as e:
                err_msg = str(e)
                self.app.after(0, lambda err=err_msg: (self.app.status.set("Error"),
                                           messagebox.showerror("Error", err)))
        run_in_thread(work)


# ── 5. PDF to JPG ─────────────────────────────────────────────────────────────
class PDF2JPGView(BaseToolView):
    def __init__(self, p, app):
        super().__init__(p, app, "PDF to JPG")
        self.zone = FileDropZone(self.body, "Select PDF to convert",
                                 multiple=True, height=120)
        self.zone.pack(fill="x", pady=4)
        labeled(self.body, "DPI (resolution):")
        self.dpi = tk.Scale(self.body, from_=72, to=300, orient="horizontal",
                             bg=BG, troughcolor="#ddd", highlightthickness=0)
        self.dpi.set(150)
        self.dpi.pack(fill="x")
        rf = tk.Frame(self.body, bg=BG)
        rf.pack(fill="x", pady=4)
        tk.Label(rf, text="Format:", bg=BG, fg=TEXT_DARK,
                 font=("Segoe UI", 10)).pack(side="left")
        self.fmt = tk.StringVar(value="JPEG")
        for v in ["JPEG", "PNG"]:
            tk.Radiobutton(rf, text=v, variable=self.fmt, value=v,
                           bg=BG, font=("Segoe UI", 10)).pack(side="left", padx=8)
        action_btn(self.body, "Convert", self._run, color="#2980b9").pack(pady=12)

    def _run(self):
        if not self.zone.files:
            return messagebox.showwarning("No files", "Select PDF files first.")
        out_dir = filedialog.askdirectory(title="Output folder")
        if not out_dir: return
        dpi = self.dpi.get()
        fmt = self.fmt.get()
        self.app.status.set("Converting…", busy=True)

        def work():
            try:
                import fitz  # PyMuPDF
                ext = ".jpg" if fmt == "JPEG" else ".png"
                for f in self.zone.files:
                    doc  = fitz.open(f)
                    base = Path(f).stem
                    mat  = fitz.Matrix(dpi/72, dpi/72)
                    for i, page in enumerate(doc):
                        pix = page.get_pixmap(matrix=mat)
                        out = os.path.join(out_dir, f"{base}_page{i+1}{ext}")
                        pix.save(out)
                self.app.after(0, lambda: (self.app.status.set("✔ Done!"),
                                           messagebox.showinfo("Done", f"Images saved to:\n{out_dir}")))
            except ImportError:
                # Fallback: use Pillow + pypdf (low quality)
                try:
                    from pypdf import PdfReader
                    from PIL import Image
                    ext = ".jpg" if fmt == "JPEG" else ".png"
                    for f in self.zone.files:
                        reader = PdfReader(f)
                        base   = Path(f).stem
                        for i, page in enumerate(reader.pages):
                            # render via xobjects / embedded images
                            imgs = list(page.images)
                            if imgs:
                                for j, img_name in enumerate(imgs):
                                    img_data = page.images[img_name].data
                                    img = Image.open(io.BytesIO(img_data))
                                    out = os.path.join(out_dir, f"{base}_p{i+1}_img{j+1}{ext}")
                                    img.save(out)
                            else:
                                # blank placeholder
                                w = int(page.mediabox.width)
                                h = int(page.mediabox.height)
                                img = Image.new("RGB", (w or 595, h or 842), "white")
                                out = os.path.join(out_dir, f"{base}_page{i+1}{ext}")
                                img.save(out)
                    self.app.after(0, lambda: (self.app.status.set("✔ Done (basic mode)!"),
                                               messagebox.showinfo("Done",
                                               f"Images saved to:\n{out_dir}\n\nNote: Install PyMuPDF (pip install pymupdf) for full rendering.")))
                except Exception as e2:
                    self.app.after(0, lambda: (self.app.status.set("Error"),
                                               messagebox.showerror("Error", str(e2))))
            except Exception as e:
                err_msg = str(e)
                self.app.after(0, lambda err=err_msg: (self.app.status.set("Error"),
                                           messagebox.showerror("Error", err)))
        run_in_thread(work)


# ── 6. JPG to PDF ─────────────────────────────────────────────────────────────
class JPG2PDFView(BaseToolView):
    def __init__(self, p, app):
        super().__init__(p, app, "JPG / Image to PDF")
        self.zone = FileDropZone(self.body,
                                 "Select images (JPG, PNG, BMP, TIFF…)",
                                 multiple=True,
                                 filetypes=[("Images","*.jpg *.jpeg *.png *.bmp *.tiff *.tif *.webp"),
                                            ("All","*.*")],
                                 height=120)
        self.zone.pack(fill="x", pady=4)

        rf = tk.Frame(self.body, bg=BG)
        rf.pack(fill="x", pady=4)
        tk.Label(rf, text="Page size:", bg=BG, fg=TEXT_DARK,
                 font=("Segoe UI", 10)).pack(side="left")
        self.size = tk.StringVar(value="fit")
        for v, lbl in [("fit","Fit to image"),("A4","A4"),("Letter","Letter")]:
            tk.Radiobutton(rf, text=lbl, variable=self.size, value=v,
                           bg=BG, font=("Segoe UI", 10)).pack(side="left", padx=6)

        action_btn(self.body, "Convert to PDF", self._run, color="#16a085").pack(pady=12)

    def _run(self):
        if not self.zone.files:
            return messagebox.showwarning("No files", "Select image files first.")
        out = filedialog.asksaveasfilename(defaultextension=".pdf",
                                           filetypes=[("PDF","*.pdf")],
                                           initialfile="images.pdf")
        if not out: return
        size = self.size.get()
        files = self.zone.files
        self.app.status.set("Converting…", busy=True)

        def work():
            try:
                from reportlab.lib.pagesizes import A4, letter
                from reportlab.pdfgen import canvas as rl_canvas
                from PIL import Image as PILImage

                if size == "A4":
                    pw, ph = A4
                elif size == "Letter":
                    pw, ph = letter
                else:
                    pw, ph = None, None

                c = None
                for f in files:
                    img = PILImage.open(f).convert("RGB")
                    iw, ih = img.size
                    if pw is None:
                        # fit to image
                        cpw, cph = float(iw), float(ih)
                    else:
                        cpw, cph = pw, ph
                    if c is None:
                        c = rl_canvas.Canvas(out, pagesize=(cpw, cph))
                    else:
                        c.setPageSize((cpw, cph))
                    # scale to fit page
                    ratio = min(cpw/iw, cph/ih)
                    nw, nh = iw*ratio, ih*ratio
                    x = (cpw - nw)/2
                    y = (cph - nh)/2
                    c.drawImage(f, x, y, width=nw, height=nh,
                                preserveAspectRatio=True)
                    c.showPage()
                if c:
                    c.save()
                self.app.after(0, lambda: (self.app.status.set("✔ Done!"),
                                           messagebox.showinfo("Done", f"Saved:\n{out}")))
            except Exception as e:
                err_msg = str(e)
                self.app.after(0, lambda err=err_msg: (self.app.status.set("Error"),
                                           messagebox.showerror("Error", err)))
        run_in_thread(work)


# ── 7. Add Watermark ─────────────────────────────────────────────────────────
class WatermarkView(BaseToolView):
    def __init__(self, p, app):
        super().__init__(p, app, "Add Watermark")
        self.zone = FileDropZone(self.body, "Select PDF(s) to watermark",
                                 multiple=True, height=120)
        self.zone.pack(fill="x", pady=4)

        labeled(self.body, "Watermark text:")
        self.txt = tk.Entry(self.body, font=("Segoe UI", 11),
                             relief="solid", bd=1)
        self.txt.insert(0, "CONFIDENTIAL")
        self.txt.pack(fill="x", pady=2)

        rf = tk.Frame(self.body, bg=BG)
        rf.pack(fill="x", pady=4)
        tk.Label(rf, text="Opacity:", bg=BG, fg=TEXT_DARK,
                 font=("Segoe UI", 10)).pack(side="left")
        self.opacity = tk.Scale(rf, from_=10, to=100, orient="horizontal",
                                bg=BG, troughcolor="#ddd", highlightthickness=0,
                                length=180)
        self.opacity.set(30)
        self.opacity.pack(side="left", padx=8)

        rf2 = tk.Frame(self.body, bg=BG)
        rf2.pack(fill="x", pady=4)
        tk.Label(rf2, text="Color:", bg=BG, fg=TEXT_DARK,
                 font=("Segoe UI", 10)).pack(side="left")
        self.color_var = tk.StringVar(value="gray")
        for v, lbl in [("gray","Gray"),("red","Red"),("blue","Blue"),("black","Black")]:
            tk.Radiobutton(rf2, text=lbl, variable=self.color_var, value=v,
                           bg=BG, font=("Segoe UI", 9)).pack(side="left", padx=6)

        action_btn(self.body, "Add Watermark", self._run, color="#d35400").pack(pady=12)

    def _run(self):
        if not self.zone.files:
            return messagebox.showwarning("No files", "Select PDF files first.")
        text = self.txt.get().strip()
        if not text:
            return messagebox.showwarning("Empty text", "Enter watermark text.")
        out_dir = filedialog.askdirectory(title="Output folder")
        if not out_dir: return
        opacity = self.opacity.get() / 100.0
        color   = self.color_var.get()
        self.app.status.set("Adding watermark…", busy=True)

        def work():
            try:
                from reportlab.lib.pagesizes import letter
                from reportlab.pdfgen import canvas as rl_canvas
                from reportlab.lib.colors import Color, red, blue, black, gray
                from pypdf import PdfReader, PdfWriter
                import math
                COLOR_MAP = {"gray": gray, "red": red, "blue": blue, "black": black}
                chosen = COLOR_MAP.get(color, gray)

                for f in self.zone.files:
                    reader = PdfReader(f)
                    writer = PdfWriter()
                    tmp    = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
                    tmp.close()

                    # build watermark PDF
                    page0  = reader.pages[0]
                    pw = float(page0.mediabox.width)
                    ph = float(page0.mediabox.height)
                    wm_c = rl_canvas.Canvas(tmp.name, pagesize=(pw, ph))
                    wm_c.saveState()
                    wm_c.setFillColor(Color(chosen.red, chosen.green, chosen.blue, alpha=opacity))
                    wm_c.setFont("Helvetica-Bold", min(pw, ph) / 8)
                    wm_c.translate(pw/2, ph/2)
                    wm_c.rotate(45)
                    wm_c.drawCentredString(0, 0, text)
                    wm_c.restoreState()
                    wm_c.save()

                    wm_page = PdfReader(tmp.name).pages[0]
                    for page in reader.pages:
                        page.merge_page(wm_page)
                        writer.add_page(page)

                    out = os.path.join(out_dir, "wm_" + os.path.basename(f))
                    with open(out, "wb") as fh:
                        writer.write(fh)
                    os.unlink(tmp.name)

                self.app.after(0, lambda: (self.app.status.set("✔ Watermarked!"),
                                           messagebox.showinfo("Done", f"Saved to:\n{out_dir}")))
            except Exception as e:
                err_msg = str(e)
                self.app.after(0, lambda err=err_msg: (self.app.status.set("Error"),
                                           messagebox.showerror("Error", err)))
        run_in_thread(work)


# ── 8. Page Numbers ───────────────────────────────────────────────────────────
class PageNumView(BaseToolView):
    def __init__(self, p, app):
        super().__init__(p, app, "Add Page Numbers")
        self.zone = FileDropZone(self.body, "Select PDF(s)",
                                 multiple=True, height=120)
        self.zone.pack(fill="x", pady=4)

        rf = tk.Frame(self.body, bg=BG)
        rf.pack(fill="x", pady=4)
        tk.Label(rf, text="Position:", bg=BG, fg=TEXT_DARK,
                 font=("Segoe UI", 10)).pack(side="left")
        self.pos = tk.StringVar(value="bottom-center")
        for v in ["bottom-center","bottom-right","bottom-left","top-center","top-right"]:
            tk.Radiobutton(rf, text=v.replace("-", " ").title(),
                           variable=self.pos, value=v,
                           bg=BG, font=("Segoe UI", 8)).pack(side="left", padx=4)

        labeled(self.body, "Start numbering from:")
        self.start = tk.Entry(self.body, font=("Segoe UI", 10),
                               relief="solid", bd=1, width=8)
        self.start.insert(0, "1")
        self.start.pack(anchor="w", pady=2)

        labeled(self.body, "Format (use {n} for number, {total} for total):")
        self.fmt = tk.Entry(self.body, font=("Segoe UI", 10),
                             relief="solid", bd=1)
        self.fmt.insert(0, "Page {n} of {total}")
        self.fmt.pack(fill="x", pady=2)

        action_btn(self.body, "Add Page Numbers", self._run, color="#2c3e50").pack(pady=12)

    def _run(self):
        if not self.zone.files:
            return messagebox.showwarning("No files", "Select PDF files first.")
        out_dir = filedialog.askdirectory(title="Output folder")
        if not out_dir: return
        pos  = self.pos.get()
        fmt  = self.fmt.get()
        try:
            start_n = int(self.start.get())
        except ValueError:
            start_n = 1
        self.app.status.set("Adding page numbers…", busy=True)

        def work():
            try:
                from reportlab.pdfgen import canvas as rl_canvas
                from pypdf import PdfReader, PdfWriter
                MARGIN = 28

                for f in self.zone.files:
                    reader = PdfReader(f)
                    total  = len(reader.pages)
                    writer = PdfWriter()
                    for i, page in enumerate(reader.pages):
                        pw = float(page.mediabox.width)
                        ph = float(page.mediabox.height)
                        tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
                        tmp.close()
                        num_txt = fmt.replace("{n}", str(i + start_n)) \
                                     .replace("{total}", str(total))
                        c = rl_canvas.Canvas(tmp.name, pagesize=(pw, ph))
                        c.setFont("Helvetica", 10)
                        c.setFillColorRGB(0.3, 0.3, 0.3)
                        if pos == "bottom-center":
                            c.drawCentredString(pw/2, MARGIN, num_txt)
                        elif pos == "bottom-right":
                            c.drawRightString(pw - MARGIN, MARGIN, num_txt)
                        elif pos == "bottom-left":
                            c.drawString(MARGIN, MARGIN, num_txt)
                        elif pos == "top-center":
                            c.drawCentredString(pw/2, ph - MARGIN, num_txt)
                        elif pos == "top-right":
                            c.drawRightString(pw - MARGIN, ph - MARGIN, num_txt)
                        c.save()
                        num_page = PdfReader(tmp.name).pages[0]
                        page.merge_page(num_page)
                        writer.add_page(page)
                        os.unlink(tmp.name)
                    out = os.path.join(out_dir, "numbered_" + os.path.basename(f))
                    with open(out, "wb") as fh:
                        writer.write(fh)
                self.app.after(0, lambda: (self.app.status.set("✔ Done!"),
                                           messagebox.showinfo("Done", f"Saved to:\n{out_dir}")))
            except Exception as e:
                err_msg = str(e)
                self.app.after(0, lambda err=err_msg: (self.app.status.set("Error"),
                                           messagebox.showerror("Error", err)))
        run_in_thread(work)


# ── 9. Protect PDF ────────────────────────────────────────────────────────────
class ProtectView(BaseToolView):
    def __init__(self, p, app):
        super().__init__(p, app, "Protect PDF (Add Password)")
        self.zone = FileDropZone(self.body, "Select PDF(s) to protect",
                                 multiple=True, height=120)
        self.zone.pack(fill="x", pady=4)
        labeled(self.body, "User password (required to open):")
        self.user_pw = tk.Entry(self.body, font=("Segoe UI", 11),
                                 show="*", relief="solid", bd=1)
        self.user_pw.pack(fill="x", pady=2)
        labeled(self.body, "Owner password (optional, for permissions):")
        self.owner_pw = tk.Entry(self.body, font=("Segoe UI", 11),
                                  show="*", relief="solid", bd=1)
        self.owner_pw.pack(fill="x", pady=2)
        action_btn(self.body, "Protect PDF", self._run, color="#c0392b").pack(pady=12)

    def _run(self):
        if not self.zone.files:
            return messagebox.showwarning("No files", "Select PDF files first.")
        upw = self.user_pw.get()
        opw = self.owner_pw.get() or upw
        if not upw:
            return messagebox.showwarning("No password", "Enter a user password.")
        out_dir = filedialog.askdirectory(title="Output folder")
        if not out_dir: return
        self.app.status.set("Encrypting…", busy=True)

        def work():
            try:
                from pypdf import PdfReader, PdfWriter
                for f in self.zone.files:
                    reader = PdfReader(f)
                    writer = PdfWriter()
                    for page in reader.pages:
                        writer.add_page(page)
                    writer.encrypt(upw, opw)
                    out = os.path.join(out_dir, "protected_" + os.path.basename(f))
                    with open(out, "wb") as fh:
                        writer.write(fh)
                self.app.after(0, lambda: (self.app.status.set("✔ Protected!"),
                                           messagebox.showinfo("Done", f"Saved to:\n{out_dir}")))
            except Exception as e:
                err_msg = str(e)
                self.app.after(0, lambda err=err_msg: (self.app.status.set("Error"),
                                           messagebox.showerror("Error", err)))
        run_in_thread(work)


# ── 10. Unlock PDF ────────────────────────────────────────────────────────────
class UnlockView(BaseToolView):
    def __init__(self, p, app):
        super().__init__(p, app, "Unlock PDF (Remove Password)")
        self.zone = FileDropZone(self.body, "Select encrypted PDF(s)",
                                 multiple=True, height=120)
        self.zone.pack(fill="x", pady=4)
        labeled(self.body, "Password:")
        self.pw = tk.Entry(self.body, font=("Segoe UI", 11),
                            show="*", relief="solid", bd=1)
        self.pw.pack(fill="x", pady=2)
        action_btn(self.body, "Unlock PDF", self._run, color="#27ae60").pack(pady=12)

    def _run(self):
        if not self.zone.files:
            return messagebox.showwarning("No files", "Select PDF files first.")
        pw = self.pw.get()
        if not pw:
            return messagebox.showwarning("No password", "Enter the PDF password.")
        out_dir = filedialog.askdirectory(title="Output folder")
        if not out_dir: return
        self.app.status.set("Unlocking…", busy=True)

        def work():
            try:
                from pypdf import PdfReader, PdfWriter
                errors = []
                for f in self.zone.files:
                    try:
                        reader = PdfReader(f)
                        if reader.is_encrypted:
                            result = reader.decrypt(pw)
                            if result == 0:
                                errors.append(f"{os.path.basename(f)}: wrong password")
                                continue
                        writer = PdfWriter()
                        for page in reader.pages:
                            writer.add_page(page)
                        out = os.path.join(out_dir, "unlocked_" + os.path.basename(f))
                        with open(out, "wb") as fh:
                            writer.write(fh)
                    except Exception as fe:
                        errors.append(f"{os.path.basename(f)}: {fe}")
                if errors:
                    msg = "Some files failed:\n" + "\n".join(errors)
                else:
                    msg = f"All files unlocked!\nSaved to:\n{out_dir}"
                self.app.after(0, lambda: (self.app.status.set("✔ Unlocked!"),
                                           messagebox.showinfo("Done", msg)))
            except Exception as e:
                err_msg = str(e)
                self.app.after(0, lambda err=err_msg: (self.app.status.set("Error"),
                                           messagebox.showerror("Error", err)))
        run_in_thread(work)


# ── 11. Organize Pages ────────────────────────────────────────────────────────
class OrganizeView(BaseToolView):
    def __init__(self, p, app):
        super().__init__(p, app, "Organize / Reorder Pages")
        self.zone = FileDropZone(self.body, "Select a PDF", height=100)
        self.zone.pack(fill="x", pady=4)
        tk.Button(self.body, text="Load Pages", command=self._load,
                  bg=ACCENT, fg="white", relief="flat",
                  font=("Segoe UI", 10, "bold"), padx=14, pady=6,
                  cursor="hand2").pack(anchor="w", pady=4)

        self.info = tk.Label(self.body, text="", bg=BG, fg=TEXT_GRAY,
                              font=("Segoe UI", 9))
        self.info.pack(anchor="w")

        labeled(self.body, "New page order (comma-separated, e.g. 3,1,2,4-6):")
        self.order_entry = tk.Entry(self.body, font=("Segoe UI", 10),
                                     relief="solid", bd=1)
        self.order_entry.pack(fill="x", pady=2)

        action_btn(self.body, "Save Reordered PDF", self._run, color="#8e44ad").pack(pady=12)
        self._total = 0

    def _load(self):
        if not self.zone.files:
            return messagebox.showwarning("No file", "Select a PDF first.")
        from pypdf import PdfReader
        try:
            r = PdfReader(self.zone.files[0])
            self._total = len(r.pages)
            self.info.config(text=f"Total pages: {self._total}")
            self.order_entry.delete(0, "end")
            self.order_entry.insert(0, ",".join(str(i) for i in range(1, self._total+1)))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _run(self):
        if not self.zone.files or not self._total:
            return messagebox.showwarning("Not loaded", "Load a PDF first.")
        raw = self.order_entry.get().strip()
        out = filedialog.asksaveasfilename(defaultextension=".pdf",
                                            filetypes=[("PDF","*.pdf")],
                                            initialfile="organized.pdf")
        if not out: return
        self.app.status.set("Organizing…", busy=True)

        def parse_order(s):
            result = []
            for part in s.split(","):
                part = part.strip()
                if "-" in part:
                    a, b = part.split("-")
                    result += list(range(int(a)-1, int(b)))
                else:
                    result.append(int(part)-1)
            return result

        def work():
            try:
                from pypdf import PdfReader, PdfWriter
                indices = parse_order(raw)
                reader  = PdfReader(self.zone.files[0])
                writer  = PdfWriter()
                for idx in indices:
                    if 0 <= idx < self._total:
                        writer.add_page(reader.pages[idx])
                with open(out, "wb") as fh:
                    writer.write(fh)
                self.app.after(0, lambda: (self.app.status.set("✔ Organized!"),
                                           messagebox.showinfo("Done", f"Saved:\n{out}")))
            except Exception as e:
                err_msg = str(e)
                self.app.after(0, lambda err=err_msg: (self.app.status.set("Error"),
                                           messagebox.showerror("Error", err)))
        run_in_thread(work)


# ── 12. Extract Text ──────────────────────────────────────────────────────────
class ExtractTextView(BaseToolView):
    def __init__(self, p, app):
        super().__init__(p, app, "Extract Text from PDF")
        self.zone = FileDropZone(self.body, "Select a PDF", height=100)
        self.zone.pack(fill="x", pady=4)
        rf = tk.Frame(self.body, bg=BG)
        rf.pack(fill="x", pady=4)
        action_btn(rf, "Extract & Preview", self._preview, color="#2980b9").pack(side="left")
        action_btn(rf, "Save as .txt", self._save, color="#2c3e50").pack(side="left", padx=8)

        self.text_box = tk.Text(self.body, font=("Courier", 9),
                                 relief="solid", bd=1, wrap="word",
                                 height=16, bg="#f8f9fa")
        sb = ttk.Scrollbar(self.body, command=self.text_box.yview)
        self.text_box.config(yscrollcommand=sb.set)
        self.text_box.pack(fill="both", expand=True, pady=4, side="left")
        sb.pack(fill="y", pady=4, side="right")

    def _extract(self):
        if not self.zone.files:
            messagebox.showwarning("No file", "Select a PDF first.")
            return None
        try:
            import pdfplumber
            text = ""
            with pdfplumber.open(self.zone.files[0]) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        text += t + "\n\n"
            return text
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return None

    def _preview(self):
        t = self._extract()
        if t is not None:
            self.text_box.delete("1.0", "end")
            self.text_box.insert("end", t or "(No text found)")

    def _save(self):
        t = self._extract()
        if t is None: return
        out = filedialog.asksaveasfilename(defaultextension=".txt",
                                            filetypes=[("Text","*.txt")],
                                            initialfile="extracted.txt")
        if not out: return
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(t)
        messagebox.showinfo("Done", f"Text saved:\n{out}")


# ── 13. Extract Images ────────────────────────────────────────────────────────
class ExtractImgView(BaseToolView):
    def __init__(self, p, app):
        super().__init__(p, app, "Extract Images from PDF")
        self.zone = FileDropZone(self.body, "Select PDF(s)",
                                 multiple=True, height=120)
        self.zone.pack(fill="x", pady=4)
        labeled(self.body, "Output format:")
        rf = tk.Frame(self.body, bg=BG)
        rf.pack(fill="x", pady=2)
        self.fmt = tk.StringVar(value="PNG")
        for v in ["PNG", "JPEG"]:
            tk.Radiobutton(rf, text=v, variable=self.fmt, value=v,
                           bg=BG, font=("Segoe UI", 10)).pack(side="left", padx=8)
        action_btn(self.body, "Extract Images", self._run, color="#16a085").pack(pady=12)

    def _run(self):
        if not self.zone.files:
            return messagebox.showwarning("No files", "Select PDF files first.")
        out_dir = filedialog.askdirectory(title="Output folder")
        if not out_dir: return
        fmt = self.fmt.get()
        self.app.status.set("Extracting images…", busy=True)

        def work():
            try:
                from pypdf import PdfReader
                from PIL import Image
                count = 0
                for f in self.zone.files:
                    reader = PdfReader(f)
                    base   = Path(f).stem
                    for pi, page in enumerate(reader.pages):
                        for ji, img_obj in enumerate(page.images):
                            img = Image.open(io.BytesIO(img_obj.data)).convert("RGB")
                            ext  = ".png" if fmt == "PNG" else ".jpg"
                            name = f"{base}_p{pi+1}_i{ji+1}{ext}"
                            img.save(os.path.join(out_dir, name))
                            count += 1
                self.app.after(0, lambda: (self.app.status.set(f"✔ {count} images extracted!"),
                                           messagebox.showinfo("Done",
                                           f"{count} image(s) saved to:\n{out_dir}")))
            except Exception as e:
                err_msg = str(e)
                self.app.after(0, lambda err=err_msg: (self.app.status.set("Error"),
                                           messagebox.showerror("Error", err)))
        run_in_thread(work)


# ── 14. PDF to Word ───────────────────────────────────────────────────────────
class PDF2WordView(BaseToolView):
    def __init__(self, p, app):
        super().__init__(p, app, "PDF to Word (.docx)")
        self.zone = FileDropZone(self.body, "Select PDF(s) to convert",
                                 multiple=True, height=120)
        self.zone.pack(fill="x", pady=4)
        tk.Label(self.body,
                 text="ℹ  Uses Microsoft Word Native Reflow (or pdf2docx fallback).",
                 bg=BG, fg=TEXT_GRAY, font=("Segoe UI", 9)).pack(anchor="w", pady=4)
        action_btn(self.body, "Convert to Word", self._run, color="#2454a4").pack(pady=12)

    def _run(self):
        if not self.zone.files:
            return messagebox.showwarning("No files", "Select PDF files first.")
        out_dir = filedialog.askdirectory(title="Output folder")
        if not out_dir: return
        self.app.status.set("Converting to Word…", busy=True)

        def work():
            try:
                for f in self.zone.files:
                    base = Path(f).stem
                    out = os.path.join(out_dir, base + ".docx")
                    _convert_pdf_to_word_smart(f, out)
                    
                self.app.after(0, lambda: (self.app.status.set("✔ Done!"),
                                           messagebox.showinfo("Done", f"Saved to:\n{out_dir}")))
            except Exception as e:
                err_msg = str(e)
                self.app.after(0, lambda err=err_msg: (self.app.status.set("Error"),
                                           messagebox.showerror("Error", err)))
        run_in_thread(work)


# ── 15. Word to PDF ───────────────────────────────────────────────────────────
class Word2PDFView(BaseToolView):
    def __init__(self, p, app):
        super().__init__(p, app, "Word to PDF (.docx → .pdf)")
        self.zone = FileDropZone(self.body, "Select Word document(s)",
                                 multiple=True,
                                 filetypes=[("Word","*.docx *.doc"),
                                             ("All","*.*")],
                                 height=120)
        self.zone.pack(fill="x", pady=4)
        tk.Label(self.body,
                 text="ℹ  Requires Microsoft Word. Ensures exact 1:1 formatting.",
                 bg=BG, fg=TEXT_GRAY, font=("Segoe UI", 9)).pack(anchor="w", pady=4)
        action_btn(self.body, "Convert to PDF", self._run, color=ACCENT).pack(pady=12)

    def _run(self):
        if not self.zone.files:
            return messagebox.showwarning("No files", "Select Word files first.")
        out_dir = filedialog.askdirectory(title="Output folder")
        if not out_dir: return
        self.app.status.set("Converting to PDF…", busy=True)

        def work():
            try:
                for f in self.zone.files:
                    base = Path(f).stem
                    out  = os.path.join(out_dir, base + ".pdf")
                    _convert_to_pdf_smart(f, out, is_ppt=False)

                self.app.after(0, lambda: (self.app.status.set("✔ Done!"),
                                           messagebox.showinfo("Done", f"Saved to:\n{out_dir}")))
            except Exception as e:
                err_msg = str(e)
                self.app.after(0, lambda err=err_msg: (self.app.status.set("Error"),
                                           messagebox.showerror("Error", err)))
        run_in_thread(work)


# ── 16. Repair PDF ────────────────────────────────────────────────────────────
class RepairView(BaseToolView):
    def __init__(self, p, app):
        super().__init__(p, app, "Repair PDF")
        self.zone = FileDropZone(self.body, "Select PDF(s) to repair",
                                 multiple=True, height=120)
        self.zone.pack(fill="x", pady=4)
        tk.Label(self.body,
                 text="ℹ  Attempts to re-write and recover readable pages from damaged PDFs.",
                 bg=BG, fg=TEXT_GRAY, font=("Segoe UI", 9), wraplength=480,
                 justify="left").pack(anchor="w", pady=4)
        action_btn(self.body, "Repair PDF", self._run, color="#f39c12").pack(pady=12)

    def _run(self):
        if not self.zone.files:
            return messagebox.showwarning("No files", "Select PDF files first.")
        out_dir = filedialog.askdirectory(title="Output folder")
        if not out_dir: return
        self.app.status.set("Repairing…", busy=True)

        def work():
            results = []
            from pypdf import PdfReader, PdfWriter
            for f in self.zone.files:
                try:
                    reader = PdfReader(f, strict=False)
                    writer = PdfWriter()
                    for page in reader.pages:
                        try:
                            writer.add_page(page)
                        except Exception:
                            pass
                    out = os.path.join(out_dir, "repaired_" + os.path.basename(f))
                    with open(out, "wb") as fh:
                        writer.write(fh)
                    results.append(f"✔ {os.path.basename(f)} → {len(reader.pages)} pages recovered")
                except Exception as e:
                    results.append(f"✘ {os.path.basename(f)}: {e}")
            msg = "\n".join(results)
            self.app.after(0, lambda: (self.app.status.set("✔ Repair done!"),
                                       messagebox.showinfo("Repair Results", msg)))
        run_in_thread(work)


# ── 17. PowerPoint to PDF ─────────────────────────────────────────────────────
class PPT2PDFView(BaseToolView):
    def __init__(self, p, app):
        super().__init__(p, app, "PowerPoint to PDF (.pptx → .pdf)")
        self.zone = FileDropZone(
            self.body,
            "Select PowerPoint file(s) (.pptx / .ppt)",
            multiple=True,
            filetypes=[("PowerPoint", "*.pptx *.ppt"), ("All", "*.*")],
            height=120,
        )
        self.zone.pack(fill="x", pady=4)

        info = (
            "ℹ  Requires Microsoft PowerPoint. Ensures exact 1:1 formatting.\n"
        )
        tk.Label(self.body, text=info, bg=BG, fg=TEXT_GRAY,
                 font=("Segoe UI", 9), justify="left").pack(anchor="w", pady=6)

        action_btn(self.body, "Convert to PDF", self._run, color="#d04423").pack(pady=14)

    def _run(self):
        if not self.zone.files:
            return messagebox.showwarning("No files", "Select PowerPoint files first.")
        out_dir = filedialog.askdirectory(title="Choose output folder")
        if not out_dir:
            return
        files    = list(self.zone.files)
        self.app.status.set("Converting PowerPoint → PDF…", busy=True)

        def work():
            try:
                for f in files:
                    base = Path(f).stem
                    out  = os.path.join(out_dir, base + ".pdf")
                    _convert_to_pdf_smart(f, out, is_ppt=True)

                self.app.after(0, lambda: (
                    self.app.status.set("✔ Conversion done!"),
                    messagebox.showinfo("Done", f"Saved to:\n{out_dir}"),
                ))
            except Exception as e:
                err_msg = str(e)
                self.app.after(0, lambda err=err_msg: (
                    self.app.status.set("Error"),
                    messagebox.showerror("Error", err),
                ))

        run_in_thread(work)


# ════════════════════════════════════════════════════════════════════════════
# Main Application
# ════════════════════════════════════════════════════════════════════════════

def _convert_to_pdf_smart(input_path, output_path, is_ppt=False):
    """
    Attempts to convert Word or PPT to PDF.
    1. Tries MS Office COM (comtypes).
    2. Falls back to LibreOffice headless via subprocess.
    3. Raises an exception if both fail.
    """
    import os
    import subprocess
    abs_in = os.path.abspath(input_path)
    abs_out = os.path.abspath(output_path)
    
    # 1. Try MS Office COM
    try:
        import comtypes.client
        import comtypes
        comtypes.CoInitialize()
        try:
            if is_ppt:
                powerpoint = comtypes.client.CreateObject("Powerpoint.Application")
                try:
                    prs = powerpoint.Presentations.Open(abs_in, WithWindow=False)
                    prs.SaveAs(abs_out, 32)
                    prs.Close()
                finally:
                    powerpoint.Quit()
            else:
                word = comtypes.client.CreateObject("Word.Application")
                word.Visible = False
                try:
                    doc = word.Documents.Open(abs_in)
                    doc.SaveAs(abs_out, FileFormat=17)
                    doc.Close()
                finally:
                    word.Quit()
            return  # Success
        finally:
            comtypes.CoUninitialize()
    except Exception:
        pass # Fallback to LibreOffice

    # 2. Try LibreOffice
    out_dir = os.path.dirname(abs_out)
    soffice_paths = [
        "soffice",
        "libreoffice", 
        "/usr/bin/soffice",
        "/usr/bin/libreoffice",
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"
    ]
    
    lo_success = False
    for p in soffice_paths:
        try:
            kwargs = {}
            if os.name == 'nt':
                kwargs['creationflags'] = 0x08000000 # CREATE_NO_WINDOW
            subprocess.run([p, "--headless", "--convert-to", "pdf", "--outdir", out_dir, abs_in], 
                           check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)
            
            # Rename if LibreOffice saves it with a different name
            base_name = os.path.splitext(os.path.basename(abs_in))[0]
            lo_out = os.path.join(out_dir, base_name + ".pdf")
            if lo_out != abs_out and os.path.exists(lo_out):
                import shutil
                shutil.move(lo_out, abs_out)
                
            if os.path.exists(abs_out):
                lo_success = True
                break
        except Exception:
            continue
            
    if lo_success:
        return
        
    raise Exception("Conversion failed.\nNeither Microsoft Office nor LibreOffice could be used.\n\nTo use this feature, please install Microsoft Office or LibreOffice (free).")

def _convert_pdf_to_word_smart(input_path, output_path):
    """
    Attempts to convert PDF to Word.
    1. Tries MS Office COM (comtypes) to use Word's Native PDF Reflow.
    2. Falls back to pdf2docx Python library.
    """
    import os
    abs_in = os.path.abspath(input_path)
    abs_out = os.path.abspath(output_path)
    
    # 1. Try MS Office COM for Native PDF Reflow
    try:
        import comtypes.client
        import comtypes
        comtypes.CoInitialize()
        try:
            word = comtypes.client.CreateObject("Word.Application")
            word.Visible = False
            try:
                # Open the PDF in Word
                doc = word.Documents.Open(abs_in)
                # Save as DOCX (FileFormat=16)
                doc.SaveAs2(abs_out, FileFormat=16)
                doc.Close()
            finally:
                word.Quit()
            return  # Success
        finally:
            comtypes.CoUninitialize()
    except Exception:
        pass # Fallback to pdf2docx
        
    # 2. Try pdf2docx (Pure Python Fallback)
    try:
        from pdf2docx import Converter
        cv = Converter(abs_in)
        cv.convert(abs_out)
        cv.close()
        return
    except ImportError:
        raise Exception("Conversion failed.\npdf2docx is not installed and MS Word is not available.\n\nPlease run 'pip install pdf2docx'")
    except Exception as e:
        raise Exception(f"Conversion failed.\n{str(e)}")

def _compress_pdf_smart(input_path, output_path, quality_slider_value):
    """
    Compresses a PDF using Ghostscript (primary) or PyMuPDF (fallback).
    quality_slider_value: 10 to 95.
    """
    import os
    import subprocess
    abs_in = os.path.abspath(input_path)
    abs_out = os.path.abspath(output_path)
    
    # Map slider to Ghostscript preset
    if quality_slider_value <= 35:
        gs_preset = "/screen" # 72 dpi
    elif quality_slider_value <= 65:
        gs_preset = "/ebook" # 150 dpi
    elif quality_slider_value <= 85:
        gs_preset = "/printer" # 300 dpi
    else:
        gs_preset = "/prepress" # max quality
        
    gs_paths = [
        "gswin64c", "gswin32c", "gs",
        r"C:\Program Files\gs\gs10.02.1\bin\gswin64c.exe",
        r"C:\Program Files\gs\gs10.01.2\bin\gswin64c.exe",
        r"C:\Program Files\gs\gs10.00.0\bin\gswin64c.exe"
    ]
    
    gs_success = False
    for p in gs_paths:
        try:
            kwargs = {}
            if os.name == 'nt':
                kwargs['creationflags'] = 0x08000000
            
            cmd = [
                p, "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.4",
                f"-dPDFSETTINGS={gs_preset}", "-dNOPAUSE", "-dQUIET", "-dBATCH",
                f"-sOutputFile={abs_out}", abs_in
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)
            if os.path.exists(abs_out):
                gs_success = True
                break
        except Exception:
            continue
            
    if gs_success:
        return
        
    # Fallback to PyMuPDF
    import fitz
    doc = fitz.open(abs_in)
    doc.save(abs_out, garbage=4, deflate=True)
    doc.close()

TOOLS = [
    ("Merge PDF",      MergeView),
    ("Split PDF",      SplitView),
    ("Compress PDF",   CompressView),
    ("Rotate PDF",     RotateView),
    ("PDF to JPG",     PDF2JPGView),
    ("JPG to PDF",     JPG2PDFView),
    ("Add Watermark",  WatermarkView),
    ("Page Numbers",   PageNumView),
    ("Protect PDF",    ProtectView),
    ("Unlock PDF",     UnlockView),
    ("Organize Pages", OrganizeView),
    ("Extract Text",   ExtractTextView),
    ("Extract Images", ExtractImgView),
    ("PDF to Word",    PDF2WordView),
    ("Word to PDF",    Word2PDFView),
    ("PPT to PDF",     PPT2PDFView),
    ("Repair PDF",     RepairView),
]


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PDF Toolkit — Offline")
        self.geometry("920x660")
        self.minsize(800, 580)
        self.config(bg=BG)
        self._build_ui()
        self.show_home()

    def _build_ui(self):
        # ── Top bar ──────────────────────────────────────────────────────────
        topbar = tk.Frame(self, bg=ACCENT, height=52)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)
        tk.Label(topbar, text="  📄 PDF Toolkit", bg=ACCENT, fg="white",
                 font=("Segoe UI", 16, "bold")).pack(side="left", padx=16)
        tk.Label(topbar, text="100% Offline — All tools, no internet needed",
                 bg=ACCENT, fg="white", font=("Segoe UI", 9)).pack(side="right", padx=16)

        # ── Content area ──────────────────────────────────────────────────────
        self.content = tk.Frame(self, bg=BG)
        self.content.pack(fill="both", expand=True)

        # ── Status bar ────────────────────────────────────────────────────────
        self.status = StatusBar(self)
        self.status.pack(fill="x", side="bottom")

        # Pre-build all tool views (hidden by default)
        self._views: dict[str, BaseToolView] = {}
        for name, cls in TOOLS:
            v = cls(self.content, self)
            self._views[name] = v

        # Home frame
        self._home = self._build_home()

    def _build_home(self):
        outer = tk.Frame(self.content, bg=BG)

        tk.Label(outer, text="What do you want to do with your PDF?",
                 bg=BG, fg=TEXT_DARK,
                 font=("Segoe UI", 14, "bold")).pack(pady=(24, 4))
        tk.Label(outer, text="Choose a tool below — everything runs offline on your computer.",
                 bg=BG, fg=TEXT_GRAY, font=("Segoe UI", 10)).pack(pady=(0, 18))

        # Scrollable grid of cards
        canvas = tk.Canvas(outer, bg=BG, highlightthickness=0)
        vsb    = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True, padx=20)

        grid_frame = tk.Frame(canvas, bg=BG)
        canvas.create_window((0, 0), window=grid_frame, anchor="nw")
        grid_frame.bind("<Configure>",
                        lambda e: canvas.config(scrollregion=canvas.bbox("all")))
        canvas.bind("<MouseWheel>",
                    lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))

        COLS = 5
        for idx, (name, _) in enumerate(TOOLS):
            row, col = divmod(idx, COLS)
            card = ToolCard(grid_frame, name,
                             command=lambda n=name: self.show_tool(n),
                             col=col)
            card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

        for c in range(COLS):
            grid_frame.columnconfigure(c, weight=1)

        return outer

    def show_home(self):
        for v in self._views.values():
            v.pack_forget()
        self._home.pack(fill="both", expand=True)
        self.status.set("Ready")

    def show_tool(self, name: str):
        self._home.pack_forget()
        for n, v in self._views.items():
            if n != name:
                v.pack_forget()
        self._views[name].pack(fill="both", expand=True)
        self.status.set(f"Tool: {name}")


if __name__ == "__main__":
    app = App()
    app.mainloop()
