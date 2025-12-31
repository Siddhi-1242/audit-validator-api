import re
from pypdf import PdfReader


def extract_acroform_data(pdf_path: str) -> dict:
    reader = PdfReader(pdf_path)
    fields = reader.get_fields() or {}

    header = {
        "company_name": None,
        "year_period_end": None,
        "completed_by": None,
        "date": None,
    }

    rows = {}

    for field_name, field in fields.items():

        label = (
            field.get("/TU")
            or field.get("/T")
            or field_name
            or ""
        ).lower()

        value = field.get("/V")
        if not value:
            continue

        value = str(value).strip()

        is_row_field = bool(re.search(r"row[_\s]?(\d+)", label))

        # ==========================
        # PAGE 1 — STRICT MATCHING
        # ==========================
        if not is_row_field:
            if "company name" in label and not header["company_name"]:
                header["company_name"] = value
                continue

            if ("year end" in label or "year period" in label) and not header["year_period_end"]:
                header["year_period_end"] = value
                continue

            if "completed by" in label and not header["completed_by"]:
                header["completed_by"] = value
                continue

            if label.startswith("date") and not header["date"]:
                header["date"] = value
                continue

        # ==========================
        # PAGE 2 — ROWS
        # ==========================
        row_match = re.search(r"row[_\s]?(\d+)", label)
        if not row_match:
            continue

        row_no = int(row_match.group(1))

        if row_no not in rows:
            rows[row_no] = {
                "business_name": None,
                "criteria_code": None,
                "transaction_type": None,
            }

        if "business" in label:
            rows[row_no]["business_name"] = value
        elif "criteria" in label or "designates" in label:
            rows[row_no]["criteria_code"] = value
        elif "transaction" in label:
            rows[row_no]["transaction_type"] = value

    return {
        "page_1": header,
        "page_2": {
            "rows": [
                rows[k]
                for k in sorted(rows.keys())
                if any(rows[k].values())
            ]
        }
    }
