import sys
import os

sys.path.append(os.path.join(os.getcwd(), "backend"))

from audit.validation.rules import validate_company_name_rule
from audit.validation.validator import validate_document

def verify():
    # 1. Test Rule Directly
    val = "ABC, Inc. & Co."
    print(f"Testing Rule with '{val}'")
    valid, err = validate_company_name_rule(val)
    print(f"Valid: {valid}, Error: {err}")
    
    if not valid:
        print("RULE FAILED")
        return

    # 2. Test Document Flow
    padding = " audit company " * 20 # Length > 200, keywords present
    text = "Company Name: ABC, Inc. & Co.\n" + padding
    print(f"Testing Document with '{text[:50]}...'")
    res = validate_document({"page_1": {"text": text}})
    
    status = res["page_1"]["fields"]["company_name"]["status"]
    value = res["page_1"]["fields"]["company_name"]["value"]
    print(f"Status: {status}")
    print(f"Value: '{value}'")
    
    if status == "FOUND_AND_VALID":
        print("SUCCESS")
    else:
        print("FAILURE")

if __name__ == "__main__":
    verify()
