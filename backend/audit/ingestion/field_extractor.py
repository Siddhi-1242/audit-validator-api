import re


# Robust Logic
KEYWORDS_AUDIT_PAGE = ["company", "audit", "year", "period"]

def extract_headers(all_pages_text: dict):
    """
    Robustly extracts headers from the first page that looks like an audit document.
    """
    extracted_data = {
         "company_name": None,
         "year_period_end": None,
         "completed_by": None,
         "date": None
    }
    extraction_metadata = {k: "NOT_FOUND" for k in extracted_data}

    # 1. Identify Target Page
    target_page_text = ""
    target_page_num = 1
    
    # Try Page 1 first
    p1 = all_pages_text.get(1, "")
    keywords_found = sum(1 for k in KEYWORDS_AUDIT_PAGE if k in p1.lower())
    
    if keywords_found >= 2:
        target_page_text = p1
        target_page_num = 1
    else:
        # Scan other pages
        found = False
        sorted_pages = sorted(all_pages_text.keys())
        for p_num in sorted_pages:
            if p_num == 1: continue
            text = all_pages_text[p_num]
            k_count = sum(1 for k in KEYWORDS_AUDIT_PAGE if k in text.lower())
            if k_count >= 2:
                target_page_text = text
                target_page_num = p_num
                found = True
                break
        
        if not found:
            # Fallback to page 1 if nothing better found, effectively empty extract
            target_page_text = p1

    print(f"[DEBUG] Selected Page {target_page_num} for extraction.")
    print(f"[DEBUG] Text sample: {target_page_text[:300]}")

    if not target_page_text:
        return extracted_data, extraction_metadata

    # 2. Robust Regex Extraction
    # Defined inside function to use local scope ease
    patterns = {
        "company_name": r"(?i)(?:company|client)\s*name[:\s]+(.*?)(?:\n|\||$)",
        "year_period_end": r"(?i)year\s*(?:/|\\)?\s*(?:period)?\s*(?:end)?[:\s]+(.*?)(?:\n|\||$)",
        "completed_by": r"(?i)(?:completed|prepared)\s*by[:\s]+(.*?)(?:\n|\||$)",
        "date": r"(?i)date(?:1_af_date)?[:\s]+(.*?)(?:\n|\||$)"
    }

    for field, pattern in patterns.items():
        match = re.search(pattern, target_page_text)
        if match:
            # Clean up the match
            raw_val = match.group(1).strip()
            # Stop at common delimiters if regex was too greedy
            # (Though non-greedy *? usually handles it stopping at newline)
            if raw_val:
                extracted_data[field] = raw_val
                extraction_metadata[field] = "FOUND"
            else:
                extracted_data[field] = None
        else:
            extracted_data[field] = None

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
