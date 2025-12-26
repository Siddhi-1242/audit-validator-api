from .rules import (
    validate_company_name_rule,
    validate_year_period_rule,
    validate_completed_by_rule,
    validate_date_rule,
    validate_business_name,
    validate_criteria_code,
    validate_transaction_type
)

# --- Status Constants ---
STATUS_PASS = "PASS"
STATUS_FAIL = "FAIL"
STATUS_PARTIAL_PASS = "PARTIAL_PASS"
STATUS_INSUFFICIENT_DATA = "INSUFFICIENT_DATA"

FIELD_STATUS_VALID = "FOUND_AND_VALID"
FIELD_STATUS_INVALID = "FOUND_BUT_INVALID"
FIELD_STATUS_NOT_FOUND = "NOT_FOUND"



def clean_value(value):
    """
    Centralized value normalization.
    Strips whitespace, removes trailing colons, collapses multiple spaces.
    """
    if not isinstance(value, str):
        return None
    
    val = value.strip()
    if val.endswith(":"):
        val = val[:-1].strip()
        
    val = " ".join(val.split())
    return val if val else None

def validate_field(value, rule_func, field_name):
    """
    Helper to validate a single field using a rule function.
    Returns a dict with 'status', 'value', 'error'.
    """
    cleaned_val = clean_value(value)
    
    if cleaned_val:
        # Field Found -> Check Validity
        is_valid, err = rule_func(cleaned_val)
        if is_valid:
            return {
                "status": FIELD_STATUS_VALID,
                "value": cleaned_val,
                "error": None
            }
        else:
            return {
                "status": FIELD_STATUS_INVALID,
                "value": cleaned_val,
                "error": err
            }
    else:
        # Field Not Found / Empty
        return {
            "status": FIELD_STATUS_NOT_FOUND,
            "value": None,
            "error": "Field not extracted or empty."
        }


def validate_page_1(data: dict):
    fields_res = {}
    
    # 1. Company Name
    fields_res["company_name"] = validate_field(
        data.get("company_name"), validate_company_name_rule, "Company Name"
    )

    # 2. Year (Period End)
    fields_res["year"] = validate_field(
        data.get("year_period_end"), validate_year_period_rule, "Year Period"
    )

    # 3. Completed By
    fields_res["completed_by"] = validate_field(
        data.get("completed_by"), validate_completed_by_rule, "Completed By"
    )

    # 4. Date
    fields_res["date"] = validate_field(
        data.get("date"), validate_date_rule, "Date"
    )

    return fields_res


def validate_page_2(data: dict):
    rows = data.get("rows", [])
    row_results = []
    
    # Identify filled rows
    filled_rows = []
    for row in rows:
        vals = [
            clean_value(row.get("business_name")),
            clean_value(row.get("criteria_code")),
            clean_value(row.get("transaction_type"))
        ]
        if any(v for v in vals if v):
            filled_rows.append(row)

    # ZERO related parties is allowed -> PASS with text note, but effectively no field status to lower the score.
    if not filled_rows:
        return {
            "status": STATUS_PASS,
            "detail": "No related party transactions disclosed (allowed).",
            "rows": []
        }

    # Validate filled rows
    for i, row in enumerate(filled_rows):
        row_fields = {}
        
        row_fields["business_person_name"] = validate_field(
            row.get("business_name"), validate_business_name, "Business Name"
        )
        row_fields["criteria_code"] = validate_field(
            row.get("criteria_code"), validate_criteria_code, "Criteria Code"
        )
        row_fields["transaction_type"] = validate_field(
            row.get("transaction_type"), validate_transaction_type, "Transaction Type"
        )
        
        row_results.append({
            "row_number": i + 1,
            "fields": row_fields
        })

    return {
        "rows": row_results
    }


def validate_document(normalized_content: dict):
    from ..ingestion.field_extractor import extract_headers

    all_errors = []

    # --- Step 1: Check for Insufficient Data ---
    # We now look at all_pages_text if available, else fallback to page_1 text
    all_pages = normalized_content.get("all_pages_text", {})
    p1_text = normalized_content.get("page_1", {}).get("text", "")
    
    # Combine all text
    full_text = "\n".join(all_pages.values()) if all_pages else p1_text
    
    # Stricter Check: Length > 200 AND Keywords
    keywords = ["audit", "period", "company", "financial", "completed by"]
    found_keywords = sum(1 for k in keywords if k in full_text.lower())
    
    if len(full_text.strip()) < 200 or found_keywords < 2:
         return {
            "overall_status": STATUS_INSUFFICIENT_DATA,
            "page_1": {},
            "page_2": {},
            "errors": [f"Document content insufficient (Len: {len(full_text.strip())}, Keywords: {found_keywords}/5)."]
        }

    # --- Step 2: Extract & Validate Headers ---
    # use robust extraction
    # fallback to just page 1 text wrapped in dict if all_pages not present (e.g. non-pdf source)
    if not all_pages:
        all_pages = {1: p1_text}
        
    p1_data, _ = extract_headers(all_pages)
    p1_res_fields = validate_page_1(p1_data)
    
    # --- Step 3: Validate Page 2 ---
    p2_content = normalized_content.get("page_2", {})
    p2_res = validate_page_2(p2_content)
    
    # --- Step 4: Aggregate Status ---
    all_statuses = []
    
    # Page 1
    for k, f_res in p1_res_fields.items():
        all_statuses.append(f_res["status"])
        if f_res["error"]:
            all_errors.append(f"Page 1 {k}: {f_res['error']}")
            
    # Page 2
    if "rows" in p2_res:
        for row in p2_res["rows"]:
            for k, f_res in row["fields"].items():
                all_statuses.append(f_res["status"])
                if f_res["error"]:
                    all_errors.append(f"Page 2 Row {row['row_number']} {k}: {f_res['error']}")
    
    has_invalid = FIELD_STATUS_INVALID in all_statuses
    has_missing = FIELD_STATUS_NOT_FOUND in all_statuses
    
    if has_invalid:
        top_status = STATUS_FAIL
    elif has_missing:
        top_status = STATUS_PARTIAL_PASS
    else:
        top_status = STATUS_PASS
        
    return {
        "overall_status": top_status,
        "page_1": {
            "fields": p1_res_fields
        },
        "page_2": p2_res,
        "errors": all_errors
    }
