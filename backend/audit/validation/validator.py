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
    fields_res = {}
    page_valid = True
    errors = []

    # 1. Company Name
    val = data.get("company_name")
    is_valid, err = validate_company_name_rule(val)
    fields_res["company_name"] = {"value": val, "valid": is_valid, "error": err}
    if not is_valid:
        errors.append(f"Company Name warning: {err}")

    # 2. Year (Period End)
    val = data.get("year_period_end")
    is_valid, err = validate_year_period_rule(val)
    fields_res["year"] = {"value": val, "valid": is_valid, "error": err}
    if not is_valid:
        errors.append(f"Year Period warning: {err}")

    # 3. Completed By
    val = data.get("completed_by")
    is_valid, err = validate_completed_by_rule(val)
    fields_res["completed_by"] = {"value": val, "valid": is_valid, "error": err}
    if not is_valid:
        errors.append(f"Completed By warning: {err}")

    # 4. Date
    val = data.get("date")
    is_valid, err = validate_date_rule(val)
    fields_res["date"] = {"value": val, "valid": is_valid, "error": err}
    if not is_valid:
        errors.append(f"Date warning: {err}")

    return {
        "status": "PASS",   # Page-1 always structurally valid
        "fields": fields_res,
        "errors": errors
    }


def validate_page_2(data: dict):
    rows = data.get("rows", [])
    row_results = []
    page_valid = True
    errors = []

    # Identify filled rows
    filled_rows = []
    for row in rows:
        vals = [
            str(row.get("business_name") or "").strip(),
            str(row.get("criteria_code") or "").strip(),
            str(row.get("transaction_type") or "").strip()
        ]
        if any(vals):
            filled_rows.append(row)

    # ✅ ZERO related parties is allowed
    if not filled_rows:
        return {
            "status": "PASS",
            "rows": [],
            "errors": ["No related party transactions disclosed (allowed)."]
        }

    # Validate filled rows
    for i, row in enumerate(filled_rows):
        row_status = True
        field_res = {}
        row_errors = []

        # Business Name
        val = row.get("business_name")
        is_valid, err = validate_business_name(val)
        field_res["business_person_name"] = {"value": val, "valid": is_valid, "error": err}
        if not is_valid:
            row_status = False
            row_errors.append(f"Row {i+1} Business Name error: {err}")

        # Criteria Code
        val = row.get("criteria_code")
        is_valid, err = validate_criteria_code(val)
        field_res["criteria_code"] = {"value": val, "valid": is_valid, "error": err}
        if not is_valid:
            row_status = False
            row_errors.append(f"Row {i+1} Criteria Code error: {err}")

        # Transaction Type
        val = row.get("transaction_type")
        is_valid, err = validate_transaction_type(val)
        field_res["transaction_type"] = {"value": val, "valid": is_valid, "error": err}
        if not is_valid:
            row_status = False
            row_errors.append(f"Row {i+1} Transaction Type error: {err}")

        if not row_status:
            page_valid = False
            errors.extend(row_errors)

        row_results.append({
            "row_number": i + 1,
            "row_status": "PASS" if row_status else "FAIL",
            "fields": field_res
        })

    return {
        "status": "PASS" if page_valid else "FAIL",
        "rows": row_results,
        "errors": errors
    }


def validate_document(normalized_content: dict):
    from ..ingestion.field_extractor import extract_page_1_headers

    all_errors = []

    # Page 1
    p1_text = normalized_content.get("page_1", {}).get("text", "")
    p1_data, _ = extract_page_1_headers(p1_text)
    p1_res = validate_page_1(p1_data)
    all_errors.extend(p1_res.get("errors", []))

    # Page 2
    p2_content = normalized_content.get("page_2", {})
    p2_res = validate_page_2(p2_content)
    all_errors.extend(p2_res.get("errors", []))

    # ✅ STRICT AND LOGIC (UNCHANGED)
    overall = "PASS" if (
        p1_res["status"] == "PASS" and
        p2_res["status"] == "PASS"
    ) else "FAIL"

    return {
        "overall_status": overall,
        "page_1": p1_res,
        "page_2": p2_res,
        "errors": all_errors
    }
