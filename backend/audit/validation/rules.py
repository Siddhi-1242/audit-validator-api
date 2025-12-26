import re
from datetime import datetime

try:
    from dateutil import parser as date_parser
except ImportError:
    date_parser = None

# --- Regex Patterns ---
# Company Name: At least one letter, allows alphanumeric, spaces, dots, commas, &, -
REGEX_COMPANY_NAME_ROBUST = r"^(?=.*[A-Za-z])[A-Za-z0-9\s.,&\-]+$"
REGEX_CRITERIA_CODE = r"^[12]\.[a-f]$"
REGEX_ALPHA_SPACES = r"^[A-Za-z\s]+$"
# Completed By: Letters, spaces, dots (for initials)
REGEX_COMPLETED_BY = r"^[A-Za-z\s.]+$"
REGEX_DATE_MMDDYYYY = r"^(0[1-9]|1[0-2])/(0[1-9]|[12]\d|3[01])/\d{4}$"

# --- Page 1 Rules ---

def validate_company_name_rule(value: str):
    """
    Validates that the company name contains only valid characters.
    Must contain at least one letter. Allows punctuation commonly found in company names.
    """
    if not isinstance(value, str):
         return False, "Invalid type."
         
    val_clean = value.strip()
    # Check for empty handled by validator, but safe to check here
    if not val_clean:
        return False, "Company name is empty."

    if not re.match(REGEX_COMPANY_NAME_ROBUST, val_clean):
        return False, "Company name must contain at least one letter and valid characters (alphanumeric, spaces, .,&,-)."
    return True, None

def validate_year_period_rule(value):
    """
    Validates Year/Period End.
    Accepts:
    1. Exact 4 digits (YYYY)
    2. MM/DD/YYYY
    3. Full text dates (e.g. September 30, 2024) via dateutil
    """
    val_str = str(value).strip() if value else ""
    if not val_str:
        return False, "Empty value."

    # 1. Strict YYYY check
    if re.match(r"^\d{4}$", val_str):
        return True, None
    
    # 2. MM/DD/YYYY
    if re.match(REGEX_DATE_MMDDYYYY, val_str):
         return True, None

    # 3. Robust Date Parsing
    if date_parser:
        try:
            # Fuzzy=False to be stricter, but we want to allow "Sept 30, 2024"
            # If string is just "202", parser might fail or parse weirdly.
            # We already checked \d{4}.
            dt = date_parser.parse(val_str)
            # Optional: Check if year is reasonable (e.g. 1900 < year < 2100)
            if 1900 < dt.year < 2100:
                return True, None
            else:
                return False, f"Date out of reasonable range (parsed year {dt.year})."
        except (ValueError, OverflowError):
            pass

    return False, "Invalid Year / Period End format. Expected YYYY, MM/DD/YYYY, or full date."

def validate_completed_by_rule(value: str):
    if not isinstance(value, str):
        return False, "Invalid type."
        
    val_clean = value.strip()
    if not val_clean:
         return False, "Empty value."

    if not re.match(REGEX_COMPLETED_BY, val_clean):
        return False, "Completed By must contain only letters, spaces, or dots."
    
    # Removed generic length < 3 check to allow initials like "AG"
    if len(val_clean) < 2: # At least 2 chars (e.g. "A.") or just "A" might be too short, assuming initials are usually 2+
         return False, "Completed By must be at least 2 characters."
         
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
