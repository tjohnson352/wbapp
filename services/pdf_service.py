# pdf_service.py file code

import fitz  # PyMuPDF library for extracting text from PDFs

def extract_pdf(file_path):
    # Extract text from the PDF using PyMuPDF
    df1 = []
    with fitz.open(file_path) as pdf:
        for page_num in range(pdf.page_count):
            page = pdf.load_page(page_num)
            text = page.get_text()
            lines = text.splitlines()  # Split text into lines
            # Filter out lines with only whitespace and remove trailing whitespace
            cleaned_lines = [line.strip() for line in lines if line.strip()]
            df1.extend(cleaned_lines)
    return df1
