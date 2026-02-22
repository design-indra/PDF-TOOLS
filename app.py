from flask import Flask, render_template, request, send_file
import os
import io
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
import img2pdf
from PIL import Image

template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=template_dir)

MAX_SIZE = 10 * 1024 * 1024  # 10MB per file

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None
    tool = request.form.get("tool", "merge")

    if request.method == "POST":
        tool = request.form.get("tool", "merge")

        try:
            # === MERGE PDF ===
            if tool == "merge":
                files = request.files.getlist("pdfs")
                files = [f for f in files if f.filename.endswith(".pdf")]
                if len(files) < 2:
                    error = "Upload minimal 2 file PDF untuk digabungkan."
                else:
                    merger = PdfMerger()
                    for f in files:
                        merger.append(io.BytesIO(f.read()))
                    buffer = io.BytesIO()
                    merger.write(buffer)
                    merger.close()
                    buffer.seek(0)
                    return send_file(buffer, mimetype="application/pdf",
                                     as_attachment=True, download_name="merged.pdf")

            # === SPLIT PDF ===
            elif tool == "split":
                file = request.files.get("pdf")
                if not file or not file.filename.endswith(".pdf"):
                    error = "Upload file PDF terlebih dahulu."
                else:
                    reader = PdfReader(io.BytesIO(file.read()))
                    total = len(reader.pages)
                    pages_input = request.form.get("pages", "").strip()

                    if pages_input:
                        # Parse halaman spesifik: "1,3,5-7"
                        page_nums = set()
                        for part in pages_input.split(","):
                            part = part.strip()
                            if "-" in part:
                                start, end = part.split("-")
                                page_nums.update(range(int(start)-1, int(end)))
                            else:
                                page_nums.add(int(part)-1)
                        page_nums = sorted([p for p in page_nums if 0 <= p < total])
                    else:
                        page_nums = list(range(total))

                    writer = PdfWriter()
                    for p in page_nums:
                        writer.add_page(reader.pages[p])
                    buffer = io.BytesIO()
                    writer.write(buffer)
                    buffer.seek(0)
                    return send_file(buffer, mimetype="application/pdf",
                                     as_attachment=True, download_name="split.pdf")

            # === COMPRESS PDF ===
            elif tool == "compress":
                file = request.files.get("pdf")
                if not file or not file.filename.endswith(".pdf"):
                    error = "Upload file PDF terlebih dahulu."
                else:
                    reader = PdfReader(io.BytesIO(file.read()))
                    writer = PdfWriter()
                    for page in reader.pages:
                        page.compress_content_streams()
                        writer.add_page(page)
                    buffer = io.BytesIO()
                    writer.write(buffer)
                    buffer.seek(0)
                    return send_file(buffer, mimetype="application/pdf",
                                     as_attachment=True, download_name="compressed.pdf")

            # === IMAGE TO PDF ===
            elif tool == "img2pdf":
                files = request.files.getlist("images")
                images = [f for f in files if f.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
                if not images:
                    error = "Upload minimal 1 gambar (JPG/PNG/WEBP)."
                else:
                    img_bytes_list = []
                    for img_file in images:
                        img = Image.open(img_file).convert("RGB")
                        buf = io.BytesIO()
                        img.save(buf, format="JPEG")
                        img_bytes_list.append(buf.getvalue())
                    pdf_bytes = img2pdf.convert(img_bytes_list)
                    buffer = io.BytesIO(pdf_bytes)
                    return send_file(buffer, mimetype="application/pdf",
                                     as_attachment=True, download_name="images.pdf")

            # === ROTATE PDF ===
            elif tool == "rotate":
                file = request.files.get("pdf")
                angle = int(request.form.get("angle", 90))
                if not file or not file.filename.endswith(".pdf"):
                    error = "Upload file PDF terlebih dahulu."
                else:
                    reader = PdfReader(io.BytesIO(file.read()))
                    writer = PdfWriter()
                    for page in reader.pages:
                        page.rotate(angle)
                        writer.add_page(page)
                    buffer = io.BytesIO()
                    writer.write(buffer)
                    buffer.seek(0)
                    return send_file(buffer, mimetype="application/pdf",
                                     as_attachment=True, download_name="rotated.pdf")

        except Exception as e:
            print(f"PDF error: {e}")
            error = f"Gagal memproses file. Pastikan file PDF tidak rusak."

    return render_template("index.html", result=result, error=error, tool=tool)

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

if __name__ == "__main__":
    app.run(debug=True)
