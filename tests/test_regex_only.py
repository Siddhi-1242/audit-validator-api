import re

REGEX_COMPANY_NAME_ROBUST = r"^(?=.*[A-Za-z])[A-Za-z0-9\s.,&\-]+$"

def test_regex():
    val = "ABC, Inc. & Co."
    print(f"Testing value: '{val}'")
    match = re.match(REGEX_COMPANY_NAME_ROBUST, val)
    print(f"Match: {match}")
    if match:
        print("MATCHED")
    else:
        print("NO MATCH")

    val_padding = "ABC, Inc. & Co. padding padding"
    print(f"Testing value with padding: '{val_padding}'")
    match_pad = re.match(REGEX_COMPANY_NAME_ROBUST, val_padding)
    print(f"Match Pad: {match_pad}")
    
    val_fail = "123456"
    print(f"Testing fail: '{val_fail}'")
    match_fail = re.match(REGEX_COMPANY_NAME_ROBUST, val_fail)
    print(f"Match Fail: {match_fail}")

if __name__ == "__main__":
    test_regex()
