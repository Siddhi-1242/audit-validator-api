import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from audit.validation.validator import validate_document

def test_full_valid():
    print("Testing FULL VALID...")
    content = {
        "page_1": {
            "text": "Company Name: Acme Corp\nYear: 2023\nCompleted By: John Doe\nDate: 01/01/2023"
        },
        "page_2": {
            "rows": [
                {"business_name": "Partner A", "criteria_code": "1.a", "transaction_type": "Sales"}
            ]
        }
    }
    res = validate_document(content)
    print(f"Status: {res['overall_status']}")
    assert res["overall_status"] == "PASS"
    print("PASS OK\n")

def test_partial_pass():
    print("Testing PARTIAL PASS (Missing Date)...")
    content = {
        "page_1": {
            "text": "Company Name: Acme Corp\nYear: 2023\nCompleted By: John Doe"
            # Missing Date
        },
        "page_2": {
            "rows": []
        }
    }
    res = validate_document(content)
    print(f"Status: {res['overall_status']}")
    assert res["overall_status"] == "PARTIAL_PASS"
    # Check that Date is NOT_FOUND
    date_status = res["page_1"]["fields"]["date"]["status"]
    print(f"Date Status: {date_status}")
    assert date_status == "NOT_FOUND"
    print("PARTIAL_PASS OK\n")

def test_fail_invalid_data():
    print("Testing FAIL (Invalid Year)...")
    content = {
        "page_1": {
            "text": "Company Name: Acme Corp\nYear: 202\nCompleted By: John Doe\nDate: 01/01/2023" 
            # Invalid Year (3 digits)
        },
        "page_2": {
            "rows": []
        }
    }
    res = validate_document(content)
    print(f"Status: {res['overall_status']}")
    assert res["overall_status"] == "FAIL"
    
    year_res = res["page_1"]["fields"]["year"]
    print(f"Year Status: {year_res['status']}, Error: {year_res['error']}")
    assert year_res["status"] == "FOUND_BUT_INVALID"
    print("FAIL OK\n")

def test_insufficient_data():
    print("Testing INSUFFICIENT DATA...")
    content = {
        "page_1": {
            "text": "   "
        },
        "page_2": {}
    }
    res = validate_document(content)
    print(f"Status: {res['overall_status']}")
    assert res["overall_status"] == "INSUFFICIENT_DATA"
    print("INSUFFICIENT_DATA OK\n")

if __name__ == "__main__":
    try:
        test_full_valid()
        test_partial_pass()
        test_fail_invalid_data()
        test_insufficient_data()
        print("ALL TESTS PASSED")
    except AssertionError as e:
        print(f"TEST FAILED: {e}")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
