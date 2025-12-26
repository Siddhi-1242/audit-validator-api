import re
from datetime import datetime

# --- Regex Patterns ---
REGEX_COMPANY_NAME_STRICT = r"^[A-Za-z\s]+$"  # Alphabetic + Spaces only
REGEX_CRITERIA_CODE = r"^[12]\.[a-f]$"
REGEX_ALPHA_SPACES = r"^[A-Za-z\s]+$"
REGEX_DATE_MMDDYYYY = r"^(0[1-9]|1[0-2])/(0[1-9]|[12]\d|3[01])/\d{4}$"

# --- Page 1 Rules ---

def validate_company_name_rule(value: str):
    """
    Validates that the company name contains only valid characters.
    Assumes value is a string if present.
    """
    if not isinstance(value, str):
         return False, "Invalid type."
         
    val_clean = value.strip()
    if not re.match(REGEX_COMPANY_NAME_STRICT, val_clean):
        return False, "Company name must contain only alphabetic characters and spaces (no numbers or symbols)."
    return True, None

def validate_year_period_rule(value):
    """
    Validates Year/Period End is exactly 4 digits (YYYY).
    """
    val_str = str(value).strip() if value else ""
    
    # Strict YYYY check
    if re.match(r"^\d{4}$", val_str):
        return True, None

    return False, "Year / Period End must be exactly 4 digits (YYYY)."

def validate_completed_by_rule(value: str):
    if not isinstance(value, str):
        return False, "Invalid type."
        
    val_clean = value.strip()
    if not re.match(REGEX_ALPHA_SPACES, val_clean):
        return False, "Completed By must contain only letters and spaces."
    if len(val_clean) < 3:
        return False, "Completed By must be at least 3 characters."
    return True, None

def validate_date_rule(value: str):
    if not isinstance(value, str):
        return False, "Invalid type."
        
    val_clean = value.strip()
    if not re.match(REGEX_DATE_MMDDYYYY, val_clean):
        return False, "Date must be in strictly MM/DD/YYYY format."
    try:
        datetime.strptime(val_clean, "%m/%d/%Y")
    except ValueError:
        return False, "Invalid calendar date."
    return True, None

# --- Page 2 Rules ---

def validate_business_name(value: str):
    if not isinstance(value, str):
         return False, "Invalid type."
    val_clean = value.strip()
    if not re.match(REGEX_ALPHA_SPACES, val_clean):
        return False, "Name must contain alphabetic characters and spaces only."
    return True, None

def validate_criteria_code(value: str):
    val_clean = str(value).strip().lower()
    if not re.match(REGEX_CRITERIA_CODE, val_clean):
        return False, "Criteria Code must be in format '1.a', '2.b' etc."
    return True, None

def validate_transaction_type(value: str):
    if not isinstance(value, str):
        return False, "Invalid type."
    val_clean = value.strip()
    if not re.match(REGEX_ALPHA_SPACES, val_clean):
        return False, "Transaction Type must be text only (no numbers/symbols)."
    return True, None
