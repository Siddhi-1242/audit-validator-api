import re
from datetime import datetime

try:
    from dateutil import parser as date_parser
except ImportError:
    date_parser = None


# ============================================================
# REGEX PATTERNS
# ============================================================

# Company Name: At least one letter, allows alphanumeric, spaces, dots, commas, &, -
REGEX_COMPANY_NAME_ROBUST = r"^(?=.*[A-Za-z])[A-Za-z0-9\s.,&\-]+$"

# Criteria Code: ONLY 1 or 2 + dot + a–f
REGEX_CRITERIA_CODE = r"^[12]\.[a-f]$"

# Completed By: Letters, spaces, dots (for initials)
REGEX_COMPLETED_BY = r"^[A-Za-z\s.]+$"

# Date: MM/DD/YY or MM/DD/YYYY
REGEX_DATE_MMDDYYYY = r"^(0[1-9]|1[0-2])/(0[1-9]|[12]\d|3[01])/(\d{2}|\d{4})$"

# Business / Person Name (FIXED – real-world safe)
REGEX_BUSINESS_NAME = r"^[A-Za-z0-9\s.&\-]+$"


# ============================================================
# PAGE 1 RULES
# ============================================================

def validate_company_name_rule(value: str):
    if not isinstance(value, str):
        return False, "Invalid type."

    val_clean = value.strip()
    if not val_clean:
        return False, "Company name is empty."

    if not re.match(REGEX_COMPANY_NAME_ROBUST, val_clean):
        return False, "Company name must contain valid characters."

    return True, None


def validate_year_period_rule(value):
    val_str = str(value).strip() if value else ""
    if not val_str:
        return False, "Empty value."

    # YYYY
    if re.match(r"^\d{4}$", val_str):
        return True, None

    # MM/DD/YY or MM/DD/YYYY
    if re.match(REGEX_DATE_MMDDYYYY, val_str):
        return True, None

    # Full textual date
    if date_parser:
        try:
            dt = date_parser.parse(val_str)
            if 1900 < dt.year < 2100:
                return True, None
        except Exception:
            pass

    return False, "Invalid Year / Period End format."


def validate_completed_by_rule(value: str):
    if not isinstance(value, str):
        return False, "Invalid type."

    val_clean = value.strip()
    if not val_clean:
        return False, "Empty value."

    if not re.match(REGEX_COMPLETED_BY, val_clean):
        return False, "Completed By must contain only letters, spaces, or dots."

    if len(val_clean) < 2:
        return False, "Completed By must be at least 2 characters."

    return True, None


def validate_date_rule(value: str):
    if not isinstance(value, str):
        return False, "Invalid type."

    val_clean = value.strip()
    if not re.match(REGEX_DATE_MMDDYYYY, val_clean):
        return False, "Date must be in MM/DD/YY or MM/DD/YYYY format."

    try:
        year_part = val_clean.split("/")[-1]
        fmt = "%m/%d/%Y" if len(year_part) == 4 else "%m/%d/%y"
        datetime.strptime(val_clean, fmt)
    except ValueError:
        return False, "Invalid calendar date."

    return True, None


# ============================================================
# PAGE 2 RULES
# ============================================================

def validate_business_name(value: str):
    if not isinstance(value, str):
        return False, "Invalid type."

    val_clean = value.strip()
    if not val_clean:
        return False, "Empty value."

    if not re.match(REGEX_BUSINESS_NAME, val_clean):
        return False, "Invalid characters in business/person name."

    return True, None


def validate_criteria_code(value: str):
    val_clean = str(value).strip().lower()
    if not re.match(REGEX_CRITERIA_CODE, val_clean):
        return False, "Criteria Code must be in format 1.a – 2.f."

    return True, None


# OPTIONAL (Recommended) – Controlled transaction types
ALLOWED_TRANSACTION_TYPES = {
    "shareholder",
    "management",
    "affiliate",
    "director",
    "employee"
}


def validate_transaction_type(value: str):
    if not isinstance(value, str):
        return False, "Invalid type."

    val_clean = value.strip().lower()
    if val_clean not in ALLOWED_TRANSACTION_TYPES:
        return False, f"Transaction Type must be one of {sorted(ALLOWED_TRANSACTION_TYPES)}"

    return True, None
