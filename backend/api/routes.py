from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import tempfile

from backend.audit.ingestion.router import ingest_document
from backend.audit.validation.validator import validate_document
from backend.audit.normalization.normalizer import normalize_for_validation

router = APIRouter()


def build_frontend_response(validation_result: dict):
    """
    Converts backend validation output into frontend-friendly response.
    Shows ONLY missing or incorrect fields.
    """
    issues = []

    # -------- Page 1 --------
    page_1_fields = validation_result.get("page_1", {}).get("fields", {})
    for field, res in page_1_fields.items():
        if res.get("status") != "FOUND_AND_VALID":
            issues.append({
                "field": field.replace("_", " ").title(),
                "message": res.get("error", "Invalid or missing value")
            })

    # -------- Page 2 --------
    page_2 = validation_result.get("page_2", {})
    for row in page_2.get("rows", []):
        for field, res in row.get("fields", {}).items():
            if res.get("status") != "FOUND_AND_VALID":
                issues.append({
                    "field": f"{field.replace('_', ' ').title()} (Row {row.get('row_number')})",
                    "message": res.get("error", "Invalid or missing value")
                })

    return {
        "overall_status": validation_result.get("overall_status"),
        "can_proceed": validation_result.get("overall_status") == "PASS",
        "issues": issues
    }


@router.post("/validate-document")
async def validate_document_endpoint(file: UploadFile = File(...)):

    allowed_exts = {".pdf", ".docx", ".xlsx", ".csv"}
    ext = os.path.splitext(file.filename)[1].lower()

    if ext not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {sorted(allowed_exts)}"
        )

    tmp_path = None

    try:
        # 1️⃣ Save file
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        # 2️⃣ Extract
        extracted_content = await ingest_document(file, tmp_path)

        if not extracted_content:
            return {
                "success": False,
                "overall_status": "INSUFFICIENT_DATA",
                "can_proceed": False,
                "issues": ["No data extracted from document"]
            }

        # 3️⃣ Normalize
        normalized_payload = normalize_for_validation(extracted_content)

        # ✅ 4️⃣ VALIDATE (DIRECT – NO ADAPTER)
        validation_result = validate_document(normalized_payload)

        # 5️⃣ Frontend response
        frontend_response = build_frontend_response(validation_result)

        return {
            "success": True,
            **frontend_response
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
