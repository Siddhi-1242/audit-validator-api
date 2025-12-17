# Run Instructions for Document Validator API

1. **Install Dependencies**
   Ensure you have Python installed. Run:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Server**
   Start the FastAPI application using Uvicorn:
   ```bash
   uvicorn main:app --reload
   ```
   The server will start at `http://127.0.0.1:8000`.

3. **Test the Endpoint**
   You can use `curl` or Postman to test the endpoint:
   
   **Endpoint:** `POST /api/validate-document`
   
   **Example (curl):**
   ```bash
   curl -X POST "http://127.0.0.1:8000/api/validate-document" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@/path/to/your/document.pdf"
   ```

   **Supported Formats:**
   - PDF (.pdf)
   - Word (.docx)
   - Excel (.xlsx) / CSV (.csv)
