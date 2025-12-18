from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import os
import uuid
from ..audit.ingestion.router import ingest_document
from ..audit.validation.validator import validate_document

router = APIRouter()

TEMP_DIR = "temp_uploads"
os.makedirs(TEMP_DIR, exist_ok=True)

@router.post("/validate-document")
async def validate_document_endpoint(file: UploadFile = File(...)):
    # Support multiple formats, validation handled by router
    allowed_exts = ['.pdf', '.docx', '.xlsx', '.csv']
    ext = os.path.splitext(file.filename)[1].lower()
    
    if ext not in allowed_exts:
         raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed: {allowed_exts}")
         
    file_id = str(uuid.uuid4())
    file_path = os.path.join(TEMP_DIR, f"{file_id}_{file.filename}")
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 1. Ingest (Normalize)
        # ingest_document handles all formats and returns Normalized Dict
        normalized_content = await ingest_document(file, file_path)
        
        # 2. Validate
        result = validate_document(normalized_content)

        return {
            "success": True,
            "isValid": result.get("isValid", False),
            "reason": result.get("reason", "Validation completed")
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
