import os

from .docx_loader import ingest_docx
from .spreadsheet_loader import ingest_spreadsheet
from .text_extractor import extract_pdf_data
from .field_extractor import extract_page_2_rows
from .acroform_extractor import extract_acroform_data


async def ingest_document(file, file_path: str) -> dict:
    """
    Router for document ingestion.

    FINAL OUTPUT CONTRACT (USED BY NORMALIZER + VALIDATOR):
    {
      "page_1": {
        company_name,
        year_period_end,
        completed_by,
        date
      },
      "page_2": {
        "rows": [
          {
            business_name,
            criteria_code,
            transaction_type
          }
        ]
      }
    }
    """

    ext = os.path.splitext(file.filename)[1].lower()

    # ============================================================
    # PDF INGESTION
    # ============================================================
    if ext == ".pdf":

        # ---------- 1️⃣ ACROFORM (Tier-1) ----------
        acro = extract_acroform_data(file_path)

        print("\n================ ACROFORM DEBUG ================")
        print("PAGE 1:", acro.get("page_1"))
        print("PAGE 2 ROWS:", acro.get("page_2", {}).get("rows"))
        print("================================================\n")

        # -------- Page 1 (FLATTENED) --------
        page_1_fields = {
            k: v
            for k, v in acro.get("page_1", {}).items()
            if v
        }

        # -------- Page 2 (FLATTENED) --------
        page_2_rows = []
        for row in acro.get("page_2", {}).get("rows", []):
            flat_row = {
                k: v
                for k, v in row.items()
                if v
            }
            if flat_row:
                page_2_rows.append(flat_row)

        # ✅ If AcroForm produced anything, RETURN HERE
        if page_1_fields or page_2_rows:
            return {
                "page_1": page_1_fields,
                "page_2": {
                    "rows": page_2_rows
                }
            }

        # ---------- 2️⃣ TEXT FALLBACK (Tier-2) ----------
        pages_text, pages_tables = extract_pdf_data(file_path)

        # Page 1 fallback (text only)
        page_1_fields = {}
        page_1_text = pages_text.get(1, "")
        if page_1_text:
            page_1_fields["raw_text"] = page_1_text

        # Page 2 fallback (tables)
        raw_table = pages_tables.get(2, [])
        rows_dicts = extract_page_2_rows(raw_table)

        page_2_rows = []
        for r in rows_dicts:
            flat_row = {}
            if r.get("business_person_name"):
                flat_row["business_name"] = r["business_person_name"]
            if r.get("criteria_code"):
                flat_row["criteria_code"] = r["criteria_code"]
            if r.get("transaction_type"):
                flat_row["transaction_type"] = r["transaction_type"]

            if flat_row:
                page_2_rows.append(flat_row)

        return {
            "page_1": page_1_fields,
            "page_2": {
                "rows": page_2_rows
            }
        }

    # ============================================================
    # DOCX
    # ============================================================
    elif ext == ".docx":
        with open(file_path, "rb") as f:
            content = f.read()
        return ingest_docx(content)

    # ============================================================
    # SPREADSHEET
    # ============================================================
    elif ext in [".xlsx", ".csv"]:
        with open(file_path, "rb") as f:
            content = f.read()
        return ingest_spreadsheet(content, file.filename)

    # ============================================================
    # UNSUPPORTED
    # ============================================================
    return {
        "page_1": {},
        "page_2": {"rows": []}
    }
