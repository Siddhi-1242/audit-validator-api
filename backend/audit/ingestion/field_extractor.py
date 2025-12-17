import re

# Page 1 Label Map
LABEL_MAP = {
    "company_name": ["company name", "client name", "company"],
    "year_period_end": ["year / period end", "period end", "year", "period"],
    "completed_by": ["completed by", "preparer", "completed-by"],
    "date": ["date"]
}

def extract_page_1_headers(text: str):
    extracted_data = {
        "company_name": None,
        "year_period_end": None,
        "completed_by": None,
        "date": None
    }
    # Using specific keys for validation usage later, though the prompt asked for "year" I'll map it.
    
    extraction_metadata = {k: "MISSING" for k in extracted_data}
    
    if not text:
        return extracted_data, extraction_metadata

    lines = text.split('\n')
    
    for line in lines:
        line_clean = line.strip()
        if not line_clean: continue
            
        for field_key, labels in LABEL_MAP.items():
            if extracted_data[field_key] is not None: continue
            
            for label in labels:
                pattern = f"^{re.escape(label)}[:\\s]+(.*)"
                match = re.match(pattern, line_clean, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    extracted_data[field_key] = value if value else ""
                    extraction_metadata[field_key] = "FOUND" if value else "FOUND_EMPTY"
                    break
    
    return extracted_data, extraction_metadata

def extract_page_2_rows(table_data: list):
    """
    Expects table_data to be a list of lists.
    We assume the PDF table has 3 columns: Name, Criteria, Transaction Type.
    We skip the header row if it detects headers.
    """
    rows = []
    
    if not table_data:
        return rows

    start_index = 0
    # Simple heuristic to skip header row if it contains "Name" or "Criteria"
    first_row = table_data[0]
    if first_row and any("name" in str(c).lower() for c in first_row):
        start_index = 1

    for i in range(start_index, len(table_data)):
        row_raw = table_data[i]
        # Clean None values to empty strings
        row_clean = [str(cell).strip() if cell else "" for cell in row_raw]
        
        # Ensure we have at least 3 columns
        if len(row_clean) < 3:
            # Pad with empty if reading failure
            row_clean += [""] * (3 - len(row_clean))
            
        rows.append({
            "row_number": i + 1, # 1-based index including header offset logic
            "business_person_name": row_clean[0],
            "criteria_code": row_clean[1],
            "transaction_type": row_clean[2]
        })
        
    return rows
