import re

# Robust Logic
KEYWORDS_AUDIT_PAGE = [
    "company",
    "company name",
    "year",
    "period",
    "completed",
    "prepared",
    "date"
]

def _extract_from_lines(lines):
    result = {
        "company_name": None,
        "year_period_end": None,
        "completed_by": None,
        "date": None
    }

    for line in lines:
        clean = line.strip()

        if not result["company_name"]:
            if len(clean) > 3 and clean.isupper() and "FORM" not in clean:
                result["company_name"] = clean

        if not result["year_period_end"]:
            if re.search(r"\b20\d{2}\b", clean):
                result["year_period_end"] = clean

        if not result["completed_by"]:
            if "prepared" in clean.lower() or "completed" in clean.lower():
                result["completed_by"] = clean

        if not result["date"]:
            if re.search(r"\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4}", clean):
                result["date"] = clean

    return result


def extract_headers(all_pages_text: dict):
    print("🔥 NEW FIELD_EXTRACTOR ACTIVE 🔥")

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

    p1 = all_pages_text.get(1, "")
    keywords_found = sum(1 for k in KEYWORDS_AUDIT_PAGE if k in p1.lower())

    if keywords_found >= 1 or len(p1.strip()) > 200:
        target_page_text = p1
        target_page_num = 1
    else:
        for p_num in sorted(all_pages_text.keys()):
            if p_num == 1:
                continue
            text = all_pages_text[p_num]
            k_count = sum(1 for k in KEYWORDS_AUDIT_PAGE if k in text.lower())
            if k_count >= 2:
                target_page_text = text
                target_page_num = p_num
                break
        else:
            target_page_text = p1

    print(f"[DEBUG] Selected Page {target_page_num} for extraction.")
    print(f"[DEBUG] Text sample: {target_page_text[:300]}")

    if not target_page_text:
        return extracted_data, extraction_metadata

    # 2. Regex Extraction
    patterns = {
        "company_name": r"(?i)(?:company|client)\s*(?:name)?\s*[:\-]?\s+([A-Za-z0-9 &.,()\-]+)",
        "year_period_end": r"(?i)(?:year|period)\s*(?:end)?\s*[:\-]?\s*([A-Za-z0-9 /\-]+)",
        "completed_by": r"(?i)(?:completed|prepared)\s*by\s*[:\-]?\s*([A-Za-z0-9 &.,]+)",
        "date": r"(?i)(?:date|dated)\s*[:\-]?\s*((?:\d{2}[\/\-]\d{2}[\/\-]\d{4})|(?:\d{1,2}\s+[A-Za-z]+\s+\d{4})|(?:[A-Za-z]+\s+\d{1,2},\s*\d{4}))"
    }

    for field, pattern in patterns.items():
        match = re.search(pattern, target_page_text)
        if match:
            raw_val = re.split(r'[\r\n]+', match.group(1))[0].split('|')[0].strip()

            if raw_val.endswith(":") or raw_val.lower() in KEYWORDS_AUDIT_PAGE:
                continue

            extracted_data[field] = raw_val
            extraction_metadata[field] = "FOUND_AND_VALID"

    # 3. Fallback Extraction
    if any(v is None for v in extracted_data.values()):
        lines = [l for l in target_page_text.splitlines() if l.strip()]
        fallback = _extract_from_lines(lines)

        for k, v in fallback.items():
            if extracted_data[k] is None and v:
                extracted_data[k] = v
                extraction_metadata[k] = "FOUND_BY_FALLBACK"

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
