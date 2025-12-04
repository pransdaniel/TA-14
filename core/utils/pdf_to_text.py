import pdfplumber
from pdf2image import convert_from_path
import pytesseract

def extract_text_from_pdf(path):
    text = ""
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text += page_text + "\n"
    except Exception as e:
        print("PDFPlumber failed:", e)
    if not text.strip():
        pages = convert_from_path(path)
        for p in pages:
            text += pytesseract.image_to_string(p) + "\n"
    return text
