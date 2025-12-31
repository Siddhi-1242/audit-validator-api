def normalize_for_validation(extracted: dict) -> dict:
    print("🔎 NORMALIZER RECEIVED:", extracted)
    return {
        "page_1": {
            "company_name": extracted.get("page_1", {}).get("company_name"),
            "year_period_end": extracted.get("page_1", {}).get("year_period_end"),
            "completed_by": extracted.get("page_1", {}).get("completed_by"),
            "date": extracted.get("page_1", {}).get("date"),
        },
        "page_2": {
            "rows": extracted.get("page_2", {}).get("rows", [])
        }
    }

