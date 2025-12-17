from .rules import (
    validate_company_name_rule,
    validate_year_period_rule,
    validate_completed_by_rule,
    validate_date_rule,
    validate_business_name,
    validate_criteria_code,
    validate_transaction_type
)

def validate_page_1(data: dict):
    # Data is expected to be the fields dict extracted from text
    # But wait, ingest returns {"text": "..."}.
    # We still need extraction logic for Page 1!
    # The prompt says "content = ingest_document(file) ... page_1_result = validate_page_1(content['page_1'])"
    # Content['page_1'] has 'text'.
    # So validate_page_1 needs to EXTRACT then VALIDATE?
    # Or should extraction happen before?
    # "3. Route Page-1 text to header parser"
    # So `validate_page_1` *orchestrates* extraction + validation?
    # Or the orchestrator does?
    # Let's keep extraction separate in the route or orchestrator.
    # I'll let `validate_page_1` accept the EXTRACTED fields dict to keep it pure.
    # The Route will handle Extraction via `field_extractor`.
    
    fields_res = {}
    page_valid = True
    
    # 1. Company Name
    val = data.get("company_name")
    is_valid, err = validate_company_name_rule(val)
    fields_res["company_name"] = {"value": val, "valid": is_valid, "error": err}
    if not is_valid: page_valid = False

    # 2. Year (Period End)
    val = data.get("year_period_end")
    is_valid, err = validate_year_period_rule(val)
    fields_res["year"] = {"value": val, "valid": is_valid, "error": err}
    if not is_valid: page_valid = False

    # 3. Completed By
    val = data.get("completed_by")
    is_valid, err = validate_completed_by_rule(val)
    fields_res["completed_by"] = {"value": val, "valid": is_valid, "error": err}
    if not is_valid: page_valid = False

    # 4. Date
    val = data.get("date")
    is_valid, err = validate_date_rule(val)
    fields_res["date"] = {"value": val, "valid": is_valid, "error": err}
    if not is_valid: page_valid = False

    return {
        "status": "PASS" if page_valid else "FAIL",
        "fields": fields_res
    }

def validate_page_2(data: dict):
    # data is expected to be the Page 2 dict from ingestion: {"rows": [...]}
    rows = data.get("rows", [])
    row_results = []
    page_valid = True

    # 1. Filter: Identify "Filled" Rows
    # A row is filled if at least ONE field corresponds to non-whitespace text.
    filled_rows = []
    
    for row in rows:
        # Check if row has any content
        has_content = False
        vals = [
            str(row.get("business_name") or "").strip(),
            str(row.get("criteria_code") or "").strip(),
            str(row.get("transaction_type") or "").strip()
        ]
        if any(v for v in vals):
            filled_rows.append(row)

    # 2. Mandatory Disclosure Rule
    # "If ZERO filled rows are detected... Page-2 validation MUST FAIL"
    if not filled_rows:
        return {
            "status": "FAIL",
            "error": "No related party rows provided. At least one row must be filled.", # Adding top level error for clarity
            "rows": []
        }

    # 3. Validation Scope: Validate ONLY filled rows
    for i, row in enumerate(filled_rows):
        row_status = True
        field_res = {}

        # 1. Business Name
        val = row.get("business_name")
        is_valid, err = validate_business_name(val)
        # Map back to business_person_name for API backward compatibility
        field_res["business_person_name"] = {"value": val, "valid": is_valid, "error": err}
        if not is_valid: row_status = False

        # 2. Criteria Code
        val = row.get("criteria_code")
        is_valid, err = validate_criteria_code(val)
        field_res["criteria_code"] = {"value": val, "valid": is_valid, "error": err}
        if not is_valid: row_status = False

        # 3. Transaction Type
        val = row.get("transaction_type")
        is_valid, err = validate_transaction_type(val)
        field_res["transaction_type"] = {"value": val, "valid": is_valid, "error": err}
        if not is_valid: row_status = False

        if not row_status: page_valid = False

        row_results.append({
            "row_number": i + 1,
            "row_status": "PASS" if row_status else "FAIL",
            "fields": field_res
        })
    
    return {
        "status": "PASS" if page_valid else "FAIL",
        "rows": row_results
    }

def validate_document(normalized_content: dict):
    # Orchestrator
    # We need to Extract Page 1 headers from the text here? 
    # The prompt implies `validate_page_1(content["page_1"])`.
    # content["page_1"] is {"text": "..."}.
    # If validate_page_1 expects extracted fields, we must extract first.
    # To avoid circular imports or redefining extraction here, pass it through.
    
    # We import extract_page_1_headers inside to avoid circular dependency if rules depends on validator
    from ..ingestion.field_extractor import extract_page_1_headers
    
    p1_text = normalized_content.get("page_1", {}).get("text", "")
    p1_data, _ = extract_page_1_headers(p1_text) # Returns data, metadata
    
    p1_res = validate_page_1(p1_data)
    
    p2_content = normalized_content.get("page_2", {})
    p2_res = validate_page_2(p2_content)
    
    overall = "PASS" if (p1_res["status"] == "PASS" and p2_res["status"] == "PASS") else "FAIL"

    return {
        "overall_status": overall,
        "page_1": p1_res,
        "page_2": p2_res
    }
