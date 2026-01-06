from .rules import (
    validate_company_name_rule,
    validate_year_period_rule,
    validate_completed_by_rule,
    validate_date_rule,
    validate_business_name,
    validate_criteria_code,
    validate_transaction_type
)

# ============================================================
# STATUS CONSTANTS
# ============================================================

STATUS_PASS = "PASS"
STATUS_FAIL = "FAIL"
STATUS_PARTIAL_PASS = "PARTIAL_PASS"
STATUS_INSUFFICIENT_DATA = "INSUFFICIENT_DATA"

FIELD_STATUS_VALID = "FOUND_AND_VALID"
FIELD_STATUS_INVALID = "FOUND_BUT_INVALID"
FIELD_STATUS_NOT_FOUND = "NOT_FOUND"

# ============================================================
# NORMALIZATION UTILS
# ============================================================

def clean_value(value):
    if not isinstance(value, str):
        return None

    val = value.strip()
    if val.endswith(":"):
        val = val[:-1].strip()

    val = " ".join(val.split())
    return val if val else None

# ============================================================
# FIELD VALIDATION (CORE ENGINE)
# ============================================================

def validate_field(value, rule_func, field_name):
    cleaned_val = clean_value(value)

    if cleaned_val is None:
        return {
            "status": FIELD_STATUS_NOT_FOUND,
            "value": None,
            "error": "Field not extracted or empty."
        }

    is_valid, err = rule_func(cleaned_val)

    if is_valid:
        if field_name == "Criteria Code":
            cleaned_val = cleaned_val.lower()

        return {
            "status": FIELD_STATUS_VALID,
            "value": cleaned_val,
            "error": None
        }

    return {
        "status": FIELD_STATUS_INVALID,
        "value": cleaned_val,
        "error": err
    }

# ============================================================
# PAGE 1 VALIDATION (DIRECT – ACROFORM)
# ============================================================

def validate_page_1(data: dict):
    return {
        "company_name": validate_field(
            data.get("company_name"),
            validate_company_name_rule,
            "Company Name"
        ),
        "year": validate_field(
            data.get("year_period_end"),
            validate_year_period_rule,
            "Year Period"
        ),
        "completed_by": validate_field(
            data.get("completed_by"),
            validate_completed_by_rule,
            "Completed By"
        ),
        "date": validate_field(
            data.get("date"),
            validate_date_rule,
            "Date"
        )
    }

# ============================================================
# PAGE 2 VALIDATION (NORMALIZED TABLE DATA)
# ============================================================

def validate_page_2(data: dict):
    rows = data.get("rows", [])

    # Case 1: Page-2 present but empty → FAIL
    if not rows:
        return {
            "status": STATUS_FAIL,
            "detail": "Related party section is empty. At least two rows are required.",
            "rows": []
        }

    # Case 2: Less than 2 rows → FAIL
    if len(rows) < 2:
        return {
            "status": STATUS_FAIL,
            "detail": "At least two related party rows are required.",
            "rows": []
        }

    validated_rows = []

    for idx, row in enumerate(rows):
        validated_rows.append({
            "row_number": idx + 1,
            "fields": {
                "business_person_name": validate_field(
                    row.get("business_name"),
                    validate_business_name,
                    "Business Name"
                ),
                "criteria_code": validate_field(
                    row.get("criteria_code"),
                    validate_criteria_code,
                    "Criteria Code"
                ),
                "transaction_type": validate_field(
                    row.get("transaction_type"),
                    validate_transaction_type,
                    "Transaction Type"
                )
            }
        })

    return {
        "status": STATUS_PASS,
        "rows": validated_rows
    }

# ============================================================
# DOCUMENT VALIDATION (FINAL ENTRY POINT)
# ============================================================

def validate_document(normalized_content: dict):
    all_errors = []
    all_statuses = []

    # -------------------------------
    # Page 1
    # -------------------------------
    page_1_data = normalized_content.get("page_1")

    if not page_1_data:
        return {
            "overall_status": STATUS_INSUFFICIENT_DATA,
            "page_1": {},
            "page_2": {},
            "errors": ["Page 1 header data missing."]
        }

    page_1_result = validate_page_1(page_1_data)

    for field, result in page_1_result.items():
        all_statuses.append(result["status"])
        if result["error"]:
            all_errors.append(f"Page 1 {field}: {result['error']}")

    # -------------------------------
    # Page 2
    # -------------------------------
    page_2_result = validate_page_2(
        normalized_content.get("page_2", {})
    )

    # Page-2 structural failure must affect overall status
    if page_2_result.get("status") == STATUS_FAIL:
        all_statuses.append(FIELD_STATUS_INVALID)
        all_errors.append(page_2_result.get("detail"))

    if "rows" in page_2_result:
        for row in page_2_result["rows"]:
            for field, result in row["fields"].items():
                all_statuses.append(result["status"])
                if result["error"]:
                    all_errors.append(
                        f"Page 2 Row {row['row_number']} {field}: {result['error']}"
                    )

    # -------------------------------
    # Final aggregation
    # -------------------------------
    if FIELD_STATUS_INVALID in all_statuses:
        overall_status = STATUS_FAIL
    elif FIELD_STATUS_NOT_FOUND in all_statuses:
        overall_status = STATUS_PARTIAL_PASS
    else:
        overall_status = STATUS_PASS

    return {
        "overall_status": overall_status,
        "page_1": {
            "fields": page_1_result
        },
        "page_2": page_2_result,
        "errors": all_errors
    }
