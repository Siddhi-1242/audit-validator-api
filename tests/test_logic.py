import sys
import os

# Appending backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.audit.validation.rules import (
    validate_company_name_rule,
    validate_year_rule,
    validate_completed_by_rule,
    validate_date_rule
)
from backend.audit.ingestion.field_extractor import extract_header_fields

def test_rules():
    print("Testing Rules...")
    
    # Company Name
    assert validate_company_name_rule("Acme Corp")[0] == True
    assert validate_company_name_rule("A")[0] == False
    assert validate_company_name_rule("")[0] == False
    print(" - Company Name: PASS")

    # Year
    assert validate_year_rule("2024")[0] == True
    assert validate_year_rule("FY24")[0] == False
    assert validate_year_rule(2025)[0] == True
    print(" - Year: PASS")

    # Completed By
    assert validate_completed_by_rule("John Doe")[0] == True
    assert validate_completed_by_rule("John123")[0] == False
    print(" - Completed By: PASS")

    # Date
    assert validate_date_rule("12/15/2025")[0] == True
    assert validate_date_rule("2025-12-15")[0] == False
    assert validate_date_rule("13/01/2025")[0] == False # Invalid Month
    print(" - Date: PASS")

def test_extraction():
    print("\nTesting Extraction...")
    sample_text = """
    Audit Worksheet
    Company Name: Global Tech LLC
    Year / Period End: 2024
    Completed By: Jane Doe
    Date: 12/20/2024
    """
    
    data, meta = extract_header_fields(sample_text)
    
    assert data["company_name"] == "Global Tech LLC"
    assert data["year_period_end"] == "2024"
    assert meta["company_name"] == "FOUND"
    
    print(" - Extraction Logic: PASS")

if __name__ == "__main__":
    try:
        test_rules()
        test_extraction()
        print("\nALL TESTS PASSED")
    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
    except Exception as e:
        print(f"\nERROR: {e}")
