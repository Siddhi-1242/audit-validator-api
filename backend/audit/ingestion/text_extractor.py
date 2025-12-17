import pdfplumber

def extract_pdf_data(pdf_file_path: str):
    """
    Extracts data from PDF.
    Returns:
        pages_text (dict): {1: "text", 2: "text"}
        pages_tables (dict): {2: [table_data]} 
    """
    pages_text = {}
    pages_tables = {}
    
    try:
        with pdfplumber.open(pdf_file_path) as pdf:
            # Page 1: Text Extraction
            if len(pdf.pages) >= 1:
                pages_text[1] = pdf.pages[0].extract_text() or ""
            
            # Page 2: Table Extraction
            if len(pdf.pages) >= 2:
                p2 = pdf.pages[1]
                pages_text[2] = p2.extract_text() or ""
                # Extract logical table
                # setting definition to capture the table structure
                extracted_table = p2.extract_table()
                if extracted_table:
                    pages_tables[2] = extracted_table
                else:
                    pages_tables[2] = []
                    
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return {}, {}
        
    return pages_text, pages_tables
