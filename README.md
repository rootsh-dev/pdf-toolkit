# PDF Toolkit — Offline

A full-featured, offline PDF tool inspired by ilovepdf.com, built entirely in Python. This toolkit allows you to perform heavy PDF manipulations securely and privately on your own machine without uploading your sensitive documents to cloud services.

## ✨ Features

- **Merge PDF:** Combine multiple PDFs in any order.
- **Split PDF:** Extract specific pages or split a PDF into separate files.
- **Compress PDF:** Reduce file size (optimized using Ghostscript if available, falling back to Python).
- **Convert to/from PDF:**
  - PDF to JPG & JPG to PDF
  - PDF to Word (.docx)
  - Word (.docx) to PDF
  - PowerPoint (.pptx) to PDF
- **Security & Organization:**
  - Protect / Encrypt PDF with a password
  - Unlock / Decrypt PDF
  - Rotate Pages
  - Organize / Delete Pages
  - Add Watermarks
  - Add Page Numbers
- **Extraction & Repair:**
  - Extract Text
  - Extract Images
  - Repair corrupted PDFs

## 🧠 Smart Formatting Engines

Unlike standard open-source tools that often mangle complex layouts, this toolkit uses **"Smart Fallbacks"** to guarantee 1:1 pixel-perfect document conversions:

1. **Microsoft Office Automation (Highest Quality):** If Microsoft Word or PowerPoint is installed on your Windows machine, the toolkit will natively hook into their COM interfaces in the background to perform flawless "PDF Reflow" and native PDF exports.
2. **LibreOffice Headless (Open Source Fallback):** If Microsoft Office is missing (e.g., on Linux), it will automatically search for LibreOffice and silently use it in the background to preserve layouts.
3. **Pure Python Fallback:** Tools like `PDF to Word` utilize `pdf2docx` out-of-the-box if no external suite is found.

## 🚀 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/rootsh-dev/pdf-toolkit.git
   cd pdf-toolkit
   ```

2. **Create a virtual environment (Recommended):**
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux/Mac:
   source venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Application:**
   ```bash
   python pdf_toolkit.py
   ```

## 🛠 Prerequisites for Best Performance

While the app works perfectly fine out-of-the-box with just the Python `requirements.txt`, installing the following will unlock its maximum potential:

*   **Microsoft Office** (Windows only) or **LibreOffice** (Windows/Linux/Mac): Guarantees perfect layout retention for Word/PPT/PDF conversions.
*   **Ghostscript:** Highly recommended for the `Compress PDF` tool. 
    *   *With Ghostscript:* The app can perform aggressive "lossy" compression on images, fonts, and structures to massively reduce file sizes.
    *   *Without Ghostscript:* The app falls back to PyMuPDF to perform "lossless" deflation and garbage collection. This ensures zero quality loss but will result in much smaller file size reductions (often just a few kilobytes).
## 🛡 Privacy

All processing is done **100% locally** on your machine. No internet connection is required, and no data ever leaves your computer.
