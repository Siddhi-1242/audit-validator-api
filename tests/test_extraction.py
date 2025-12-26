import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from audit.validation.validator import validate_document

def test_page_scanning():
    print("Testing PAGE SCANNING Logic...")
    
    # Mock content: Page 1 is junk, Page 3 has real data
    content = {
        "page_1": {
            "text": "This is a cover page.\nNo audit info here."
        },
        "all_pages_text": {
            1: "This is a cover page.\nNo audit info here.",
            2: "Table of Contents...",
            3: "AUDIT REPORT\nCompany Name: Valid Corp\nYear End: 2023\nCompleted By: Jane Doe\nDate: 02/02/2023"
        },
        "page_2": {"rows": []}
    }
    
    res = validate_document(content)
    print(f"Status: {res['overall_status']}")
    
    # Check if it found Company Name from Page 3
    comp_name = res["page_1"]["fields"]["company_name"]["value"]
    print(f"Extracted Company: {comp_name}")
    
    assert comp_name == "Valid Corp"
    # Page 2 empty rows -> PASS (with note) if fields are valid.
    
    # Check if we got the expected PASS
    print(f"Final Status: {res['overall_status']}")
    assert res["overall_status"] == "PASS"
    print("PAGE SCANNING OK\n")

def test_robust_regex_spacing():
    print("Testing ROBUST REGEX (Spacing)...")
    
    text = "Company    Name :   Spaced Corp   | Year  Period  End : 2023"
    content = {
        "page_1": {"text": text},
        "all_pages_text": {1: text},
        "page_2": {"rows": []}
    }
    
    res = validate_document(content)
    comp = res["page_1"]["fields"]["company_name"]["value"]
    year = res["page_1"]["fields"]["year"]["value"]
    
    print(f"Company: '{comp}', Year: '{year}'")
    assert comp == "Spaced Corp"
    assert year == "2023"
    print("ROBUST REGEX OK\n")

def test_missing_field_preservation():
    print("Testing MISSING FIELD PRESERVATION...")
    
    # Missing Date
    text = "Company Name: A Corp\nYear: 2023\nCompleted By: Me" + "\n" + ("padding " * 10)
    content = {
        "page_1": {"text": text},
        "all_pages_text": {1: text},
        "page_2": {"rows": []}
    }
    
    res = validate_document(content)
    date_res = res["page_1"]["fields"]["date"]
    
    print(f"Date Status: {date_res['status']}")
    assert date_res["status"] == "NOT_FOUND" 
    assert date_res["value"] is None
    print("MISSING FIELD OK\n")

if __name__ == "__main__":
    try:
        test_page_scanning()
        test_robust_regex_spacing()
        test_missing_field_preservation()
        print("ALL EXTRACTION TESTS PASSED")
    except AssertionError as e:
        print(f"TEST FAILED: {e}")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
