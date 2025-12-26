import sys
import os

sys.path.append(os.path.join(os.getcwd(), "backend"))

from audit.validation.validator import validate_document

PADDING = "\n" + ("Audit Company " * 50) # Ensure sufficient data

def test_company_name_regex():
    print("Testing COMPANY NAME Regex...")
    
    # Valid: Punctuation, Suffixes
    t1 = "Company Name: ABC Inc Co\n" + PADDING
    res1 = validate_document({"page_1": {"text": t1}})
    val1 = res1["page_1"]["fields"]["company_name"]
    print(f"1. 'ABC, Inc. & Co.' -> {val1['status']}")
    if val1["status"] != "FOUND_AND_VALID":
        val = val1.get('value')
        print(f"   Value: {repr(val)}")
        print(f"   Chars: {[ord(c) for c in val]}")
        print(f"   Error: {repr(val1.get('error'))}")
    assert val1["status"] == "FOUND_AND_VALID"
    
    # Invalid: Pure Numeric
    t2 = "Company Name: 123456" + PADDING
    res2 = validate_document({"page_1": {"text": t2}})
    val2 = res2["page_1"]["fields"]["company_name"]
    print(f"2. '123456' -> {val2['status']} ({val2.get('error')})")
    assert val2["status"] == "FOUND_BUT_INVALID"
    
    print("COMPANY NAME OK\n")

def test_date_parsing_year():
    print("Testing YEAR/PERIOD Processing...")
    
    # Valid: Text Date
    t1 = "Year: September 30, 2024" + PADDING
    res1 = validate_document({"page_1": {"text": t1}})
    val1 = res1["page_1"]["fields"]["year"]
    print(f"1. 'September 30, 2024' -> {val1['status']}")
    assert val1["status"] == "FOUND_AND_VALID"
    
    # Valid: YYYY
    t2 = "Year: 2024" + PADDING
    res2 = validate_document({"page_1": {"text": t2}})
    val2 = res2["page_1"]["fields"]["year"]
    print(f"2. '2024' -> {val2['status']}")
    assert val2["status"] == "FOUND_AND_VALID"

    # Invalid: Garbage
    t3 = "Year: 202" + PADDING
    res3 = validate_document({"page_1": {"text": t3}})
    val3 = res3["page_1"]["fields"]["year"]
    print(f"3. '202' -> {val3['status']}")
    assert val3["status"] == "FOUND_BUT_INVALID"

    print("YEAR OK\n")

def test_completed_by_initials():
    print("Testing COMPLETED BY Initials...")
    
    t1 = "Completed By: AG" + PADDING
    res1 = validate_document({"page_1": {"text": t1}})
    val1 = res1["page_1"]["fields"]["completed_by"]
    print(f"1. 'AG' -> {val1['status']}")
    assert val1["status"] == "FOUND_AND_VALID"
    
    t2 = "Completed By: A. Green" + PADDING
    res2 = validate_document({"page_1": {"text": t2}})
    val2 = res2["page_1"]["fields"]["completed_by"]
    print(f"2. 'A. Green' -> {val2['status']}")
    assert val2["status"] == "FOUND_AND_VALID"
    
    print("COMPLETED BY OK\n")

def test_label_bleed_guard():
    print("Testing LABEL BLEED GUARD...")
    
    # Case: Captured strictly next label with colon
    t1 = "Company Name: Year Period End:" + PADDING
    res1 = validate_document({"page_1": {"text": t1}})
    val1 = res1["page_1"]["fields"]["company_name"]
    print(f"1. Bleed 'Year Period End:' -> {val1['status']}")
    assert val1["status"] == "NOT_FOUND"
    
    print("BLEED GUARD OK\n")

def test_insufficient_data_strict():
    print("Testing INSUFFICIENT DATA Strict...")
    
    # Short text, no keywords
    t1 = "Hello world this is too short"
    res1 = validate_document({"page_1": {"text": t1}})
    print(f"1. Short Text -> {res1['overall_status']}")
    assert res1["overall_status"] == "INSUFFICIENT_DATA"
    
    # Long text BUT no keywords
    t2 = ("Current events update " * 20) 
    res2 = validate_document({"page_1": {"text": t2}})
    print(f"2. Long Text No Keywords -> {res2['overall_status']}")
    assert res2["overall_status"] == "INSUFFICIENT_DATA"
    
    print("INSUFFICIENT DATA OK\n")

if __name__ == "__main__":
    try:
        test_company_name_regex()
        test_date_parsing_year()
        test_completed_by_initials()
        test_label_bleed_guard()
        test_insufficient_data_strict()
        print("ALL REFINED TESTS PASSED")
    except AssertionError as e:
        print(f"TEST FAILED: {e}")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
