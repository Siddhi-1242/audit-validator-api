import os
from .docx_loader import ingest_docx
from .spreadsheet_loader import ingest_spreadsheet
from .text_extractor import extract_pdf_data
# We need to adapt pdf extractor to the new contract here or import it
from .field_extractor import extract_page_2_rows

async def ingest_document(file, file_path: str) -> dict:
    """
    Router for document ingestion.
    Normalizes output to Page 1 Text and Page 2 Rows.
    """
    ext = os.path.splitext(file.filename)[1].lower()
    
    if ext == '.pdf':
        # Reuse existing logic but normalize the output structure here
        # extract_pdf_data returns: pages_text, pages_tables
        pages_text, pages_tables = extract_pdf_data(file_path)
        
        p1_text = pages_text.get(1, "")
        
        # We need to convert the raw table data (list of lists) into our dict structure 
        # But wait, existing extract_page_2_rows DOES that conversion.
        # But the NEW validator expects "business_name" key not "business_person_name"?
        # Let's check the contract. The NEW contract asks for "business_name".
        # Existing logic uses "business_person_name".
        # We should map it here or update extract_page_2_rows.
        
        raw_table = pages_tables.get(2, [])
        # We use the existing helper to parse the table list-of-lists
        rows_dicts = extract_page_2_rows(raw_table) 
        # Now we might need to key-map if the previous code used different keys.
        # Check field_extractor.py: keys are 'business_person_name'.
        # Contract wants: 'business_name'.
        
        # Remap for consistency
        normalized_rows = []
        for r in rows_dicts:
            normalized_rows.append({
                "business_name": r.get("business_person_name"),
                "criteria_code": r.get("criteria_code"),
                "transaction_type": r.get("transaction_type")
            })

        return {
            "page_1": {"text": p1_text},
            "page_2": {"rows": normalized_rows},
            "all_pages_text": pages_text  # Pass full text for robust header extraction
        }
        
    elif ext == '.docx':
        # We need to read the file bytes
        # Since file is an UploadFile, but we saved it to file_path
        with open(file_path, "rb") as f:
            content = f.read()
        return ingest_docx(content)
        
    elif ext in ['.xlsx', '.csv']:
        with open(file_path, "rb") as f:
            content = f.read()
        return ingest_spreadsheet(content, file.filename)
        
    else:
        # Unsupported - Validator orchestrator should handle empty/malformed
        return {
             "page_1": {"text": ""},
             "page_2": {"rows": []}
        }
