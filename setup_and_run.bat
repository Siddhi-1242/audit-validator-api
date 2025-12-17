@echo off
echo ==========================================
echo Setting up Audit PDF Validator Environment
echo ==========================================

cd audit_pdf_validator

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate

echo Installing dependencies...
pip install -r requirements.txt

echo.
echo ==========================================
echo Starting Application...
echo ==========================================
echo Frontend will be available at: http://127.0.0.1:8000
echo.

python -m backend.main
