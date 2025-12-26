import pdfplumber

def extract_pdf_data(pdf_file_path: str):
    """
    Extracts data from PDF.
    Returns:
        pages_text (dict): {page_num (int): "text"} for ALL pages.
        pages_tables (dict): {2: [table_data]} (Legacy support for Page 2 table)
    """
    pages_text = {}
    pages_tables = {}
    
    try:
        with pdfplumber.open(pdf_file_path) as pdf:
            # Extract text from ALL pages
            for i, page in enumerate(pdf.pages):
                page_num = i + 1
                text = page.extract_text() or ""
                pages_text[page_num] = text
            
            # Legacy: Page 2 Table Extraction (keep existing logic)
            if len(pdf.pages) >= 2:
                p2 = pdf.pages[1]
                extracted_table = p2.extract_table()
                if extracted_table:
                    pages_tables[2] = extracted_table
                else:
                    pages_tables[2] = []
                    
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return {}, {}
        
    return pages_text, pages_tables
