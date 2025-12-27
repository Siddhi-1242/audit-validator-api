import re
from typing import Dict, Tuple, Any, List

def extract_headers(all_pages_text: Dict[Any, str]) -> Tuple[Dict[str, str], Dict[str, Any]]:
    """
    Extracts header fields from the provided text of all pages.
    Scans the entire document line by line and keeps the last valid non-empty value found
    for each field.
    
    Fields extracted:
      - company_name
      - year_period_end
      - completed_by
      - date
    
    Returns:
        (extracted_data, extraction_metadata)
    """

    # 1. Define Fields and their Aliases
    field_definitions = {
        "company_name": [
            r"Company\s*Name"
        ],
        "year_period_end": [
            r"Year\s*/\s*Period\s*End",
            r"Year\s*End",
            r"Period\s*End"
        ],
        "completed_by": [
            r"Completed\s*By",
            r"Prepared\s*By"
        ],
        "date": [
            r"Date1_af_date",
            r"Dated",
            r"Date"
        ]
    }

    # Pre-compile regexes for each field
    field_regexes = {}
    for field, aliases in field_definitions.items():
        sorted_aliases = sorted(aliases, key=len, reverse=True)
        escaped_aliases = [re.escape(a).replace(r'\ ', r'\s*') for a in sorted_aliases]
        pattern_str = r"(?i)(?:" + "|".join(escaped_aliases) + r")\s*[:]\s*(?P<value>.*)"
        field_regexes[field] = re.compile(pattern_str)

    # Date Validation Pattern
    DATE_PATTERN = re.compile(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\w+\s+\d{1,2},\s*\d{4})\b")

    # 2. Sort pages to ensure deterministic processing order
    try:
        sorted_page_keys = sorted(all_pages_text.keys(), key=lambda x: int(x) if str(x).isdigit() else x)
    except Exception:
        sorted_page_keys = sorted(all_pages_text.keys(), key=str)

    extracted_data = {
        "company_name": None,
        "year_period_end": None,
        "completed_by": None,
        "date": None
    }
    
    debug_log = []

    # 3. Scan line by line
    for page_key in sorted_page_keys:
        text = all_pages_text.get(page_key, "")
        if not text:
            continue
            
        lines = text.splitlines()
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue

            for field, regex in field_regexes.items():
                match = regex.search(line)
                if match:
                    raw_val = match.group("value").strip()
                    
                    # --- Validation Logic ---
                    
                    # Rule 1: Reject empty
                    if not raw_val:
                        continue
                        
                    # Clean punctuation (leading and trailing)
                    clean_val = raw_val.lstrip("/: ").rstrip(".,;")
                    if not clean_val:
                        continue
                    
                    # Rule 2: Digit check for year/date
                    if field in ("year_period_end", "date") and not re.search(r"\d", clean_val):
                        continue

                    # Rule 3: Strict Date Extraction
                    if field == "date":
                        date_match = DATE_PATTERN.search(clean_val)
                        if date_match:
                            clean_val = date_match.group(1)
                        else:
                            continue

                    # Reference Rule: Last valid occurrence wins
                    extracted_data[field] = clean_val
                    debug_log.append(f"Page {page_key} [{field}]: {clean_val}")

    metadata = {
        "debug_log": debug_log,
        "scanned_pages": len(sorted_page_keys)
    }

    return extracted_data, metadata


def extract_page_2_rows(table_data: List[List[Any]]) -> List[Dict[str, Any]]:
    """
    Extracts row data from the provided 2D table structure (list of lists).
    Assumes columns: Business Person Name, Criteria Code, Transaction Type.
    
    Improvements:
    - Skips empty rows.
    - Dynamically detects/skips header row.
    - Ensures valid 3-column output structure.
    """
    rows = []
    if not table_data:
        return rows

    # 1. Detect and skip header
    start_index = 0
    header_keywords = {"name", "criteria", "transaction", "type", "business"}
    
    # Check first row
    first_row = table_data[0]
    if first_row:
        # Convert row to a single lowercase string to check for keywords
        row_str = " ".join([str(c).lower() for c in first_row if c])
        if any(keyword in row_str for keyword in header_keywords):
            start_index = 1

    current_row_id = 1
    
    for i in range(start_index, len(table_data)):
        row_raw = table_data[i]
        
        # Normalize cells: None -> "", strip whitespace
        row_clean = [str(cell).strip() if cell is not None else "" for cell in row_raw]
        
        # Skip completely empty rows
        if not any(row_clean):
            continue
            
        # Ensure at least 3 columns (pad if necessary)
        if len(row_clean) < 3:
            row_clean += [""] * (3 - len(row_clean))
            
        rows.append({
            "row_number": current_row_id,
            "business_person_name": row_clean[0],
            "criteria_code": row_clean[1],
            "transaction_type": row_clean[2]
        })
        current_row_id += 1
        
    return rows