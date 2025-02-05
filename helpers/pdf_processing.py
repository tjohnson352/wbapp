import fitz  

def extract_pdf_content(filepath):
    with fitz.open(filepath) as pdf:
        data = []
        for page_num in range(pdf.page_count):
            page = pdf.load_page(page_num)
            data.extend(page.get_text().splitlines())
        return [line.strip() for line in data if line.strip()]
