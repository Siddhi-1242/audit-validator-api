import pandas as pd
import io

def ingest_spreadsheet(file_bytes: bytes, filename: str) -> dict:
    """
    Ingests XLSX or CSV.
    Page 1: "Key: Value" dump of the first sheet/dataframe.
    Page 2: Rows from 2nd sheet (XLSX) or heuristic separation (CSV).
    """
    text_content = ""
    rows_data = []

    try:
        if filename.endswith('.xlsx'):
            xls = pd.ExcelFile(io.BytesIO(file_bytes))
            sheet_names = xls.sheet_names
            
            # Page 1: Sheet 1 contents
            if len(sheet_names) > 0:
                df1 = pd.read_excel(xls, sheet_names[0])
                # Convert to string representation for header extraction
                # We iterate rows and join them "col: val" or just space separated
                for _, row in df1.iterrows():
                    row_str = " ".join([str(x) for x in row if pd.notna(x)])
                    text_content += row_str + "\n"

            # Page 2: Sheet 2 contents (Preferred) OR look for table in Sheet 1
            if len(sheet_names) > 1:
                df2 = pd.read_excel(xls, sheet_names[1])
                rows_data = _df_to_rows(df2)
            else:
                # Fallback: if only 1 sheet, maybe the table is at the bottom?
                # For now, if 1 sheet, we assume it contains everything. 
                # But strict separation is safer. If 1 sheet, maybe no table data?
                pass
                
        else: # CSV
            df = pd.read_csv(io.BytesIO(file_bytes))
            # Treat whole CSV as text for headers AND check for table structure?
            # Audit CSVs usually either Header OR Table. 
            # Strategy: Dump all as text for Page 1.
            # Look for "Business Name" column to start Page 2 rows.
            
            # Text dump
            text_content = df.to_string(index=False)
            
            # Table extraction attempt
            rows_data = _df_to_rows(df)

    except Exception as e:
        print(f"Spreadsheet error: {e}")
        # Return empty on failure so validator fails gracefully
        pass

    return {
        "page_1": {"text": text_content},
        "page_2": {"rows": rows_data}
    }

def _df_to_rows(df):
    """
    Converts DataFrame to standardized list of dicts.
    Expects columns 1, 2, 3 to correspond to our required fields.
    """
    result = []
    # Clean NaN
    df = df.fillna("")
    
    # If columns contain "Name", "Criteria" etc, map them?
    # Simple strategy: Take first 3 columns
    if df.shape[1] < 3:
        return []
        
    for _, row in df.iterrows():
        # Convert to list
        vals = [str(x).strip() for x in row]
        result.append({
            "business_name": vals[0],
            "criteria_code": vals[1],
            "transaction_type": vals[2]
        })
    return result
