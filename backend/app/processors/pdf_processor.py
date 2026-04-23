import pdfplumber
from app.processors.text_processor import process_text


def process_pdf(file_path: str) -> dict:
    with pdfplumber.open(file_path) as pdf:
        text = " ".join((p.extract_text() or "") for p in pdf.pages)
        page_count = len(pdf.pages)
    out = process_text(text)
    out["type"] = "pdf"
    out["meta"]["page_count"] = page_count
    return out
