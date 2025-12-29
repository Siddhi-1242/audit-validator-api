import re
from typing import Dict, Tuple, Any


# ============================================================
# Validation Gate (USED BY ALL EXTRACTORS)
# ============================================================

def _is_valid_value(field: str, value: str) -> bool:
    if not value:
        return False

    value = value.strip()
    if len(value) < 3:
        return False

    if field == "company_name":
        # Must contain at least one alphabet
        if not any(c.isalpha() for c in value):
            return False
        # Reject generic placeholders
        if value.lower() in {
            "company", "company name", "client", "business", "name"
        }:
            return False

    return True


# ============================================================
# PAGE 1 – HEADER EXTRACTION (DETERMINISTIC & IMMUTABLE)
# ============================================================

def extract_headers(
    all_pages_text: Dict[Any, str]
) -> Tuple[Dict[str, str], Dict[str, Any]]:

    field_definitions = {
        "company_name": [r"Company\s*Name"],
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
            r"Dated",
            r"Date"
        ]
    }

    field_regexes = {}
    for field, aliases in field_definitions.items():
        aliases = sorted(aliases, key=len, reverse=True)
        escaped = [re.escape(a).replace(r"\ ", r"\s*") for a in aliases]
        pattern = (
            r"(?i)(?:"
            + "|".join(escaped)
            + r")\s*[:\n]?\s*(?P<value>.*)"
        )
        field_regexes[field] = re.compile(pattern)

    DATE_PATTERN = re.compile(
        r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\w+\s+\d{1,2},\s*\d{4})\b"
    )

    # Deterministic page order
    try:
        page_keys = sorted(
            all_pages_text.keys(),
            key=lambda x: int(x) if str(x).isdigit() else str(x)
        )
    except Exception:
        page_keys = sorted(all_pages_text.keys(), key=str)

    extracted_data = {
        "company_name": None,
        "year_period_end": None,
        "completed_by": None,
        "date": None
    }

    debug_log = []

    for page_key in page_keys:
        text = all_pages_text.get(page_key, "")
        if not text:
            continue

        lines = text.splitlines()

        for idx, line in enumerate(lines):
            if not line.strip():
                continue

            for field, regex in field_regexes.items():

                # IMMUTABILITY: once locked, never overwrite
                if extracted_data[field] is not None:
                    continue

                for match in regex.finditer(line):
                    raw_val = match.group("value").strip()

                    # Try next line if empty
                    if not raw_val and idx + 1 < len(lines):
                        raw_val = lines[idx + 1].strip()

                    raw_val = raw_val.replace("\u00A0", " ")
                    raw_val = re.sub(r"\s+", " ", raw_val)

                    if not raw_val:
                        continue

                    clean_val = raw_val.lstrip("/: ").rstrip(".,;")
                    if not clean_val:
                        continue

                    if field in ("year_period_end", "date") and not re.search(r"\d", clean_val):
                        continue

                    if field == "date":
                        date_match = DATE_PATTERN.search(clean_val)
                        if not date_match:
                            continue
                        clean_val = date_match.group(1)

                    if _is_valid_value(field, clean_val):
                        extracted_data[field] = clean_val
                        debug_log.append(
                            f"[LOCKED] Page {page_key} [{field}] = {clean_val}"
                        )
                        break

    # Normalize output
    for k in extracted_data:
        if extracted_data[k] is None:
            extracted_data[k] = "NOT_FOUND"

    metadata = {
        "scanned_pages": len(page_keys),
        "debug_log": debug_log
    }

    return extracted_data, metadata


# ============================================================
# PAGE 2 – RELATED PARTY DATA (ALREADY GOOD, JUST CLEANED)
# ============================================================

def extract_page_2_data(
    all_pages_text: dict
) -> Tuple[Dict[str, str], Dict]:

    extracted_data = {
        "business_name": None,
        "criteria_code": None,
        "transaction_type": None
    }

    extraction_metadata = {}

    # ⚠️ Ensure correct variable name
    target_page_text = all_pages_text.get("page_2", {}).get("text", "")
    if not target_page_text:
        return {
            k: "NOT_FOUND" for k in extracted_data
        }, {"page_2": "NOT_FOUND"}

    patterns = {
        "business_name": [
            r"Business\s*/?\s*Person's\s*Name\s*:?\s*(.+)",
            r"Name\s*of\s*Related\s*Party\s*:?\s*(.+)"
        ],
        "criteria_code": [
            r"Criteria\s*Code\s*:?\s*(.+)",
            r"\b([12]\.[a-f])\b"
        ],
        "transaction_type": [
            r"Type\s*of\s*Transactions.*?:\s*(.+)",
            r"Nature\s*of\s*Transactions\s*:?\s*(.+)"
        ]
    }

    for field, field_patterns in patterns.items():
        for pattern in field_patterns:
            for match in re.finditer(pattern, target_page_text, re.IGNORECASE):

                if extracted_data[field] is not None:
                    continue

                raw_val = match.group(1).strip()
                if _is_valid_value(field, raw_val):
                    extracted_data[field] = raw_val
                    extraction_metadata[field] = "FOUND_AND_VALID"
                    print(f"[LOCKED-P2] {field} = {raw_val}")

            if extracted_data[field] is not None:
                break

    for field in extracted_data:
        if extracted_data[field] is None:
            extracted_data[field] = "NOT_FOUND"
            extraction_metadata[field] = "NOT_FOUND"

    return extracted_data, extraction_metadata
