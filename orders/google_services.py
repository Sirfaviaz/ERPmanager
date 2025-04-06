import gspread
from google.oauth2.service_account import Credentials
from gspread.utils import rowcol_to_a1

def ranges_intersect(a, b):
    """
    Checks whether two ranges (dicts with startRowIndex, endRowIndex, etc.) intersect.
    Note: endRowIndex and endColumnIndex are exclusive.
    """
    return not (
        a["endRowIndex"] <= b["startRowIndex"]
        or a["startRowIndex"] >= b["endRowIndex"]
        or a["endColumnIndex"] <= b["startColumnIndex"]
        or a["startColumnIndex"] >= b["endColumnIndex"]
    )

def safe_merge_cells(worksheet, start_row, start_col, end_row, end_col):
    """
    Safely unmerges any merged regions that intersect with the target range,
    then merges the target range.
    
    Parameters (all 1-based):
      start_row, start_col: top-left cell of the target range.
      end_row, end_col: Exclusive boundaries (e.g., to merge rows 7–8, pass start_row=7, end_row=9).
    """
    sheet_id = worksheet._properties['sheetId']
    metadata = worksheet.spreadsheet.fetch_sheet_metadata()
    merges = []
    for sheet in metadata["sheets"]:
        if sheet["properties"]["sheetId"] == sheet_id:
            merges = sheet.get("merges", [])
            break

    target_range = {
        "startRowIndex": start_row - 1,
        "endRowIndex": end_row,
        "startColumnIndex": start_col - 1,
        "endColumnIndex": end_col
    }
    
    requests = []
    for m in merges:
        if ranges_intersect(m, target_range):
            requests.append({
                "unmergeCells": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": m["startRowIndex"],
                        "endRowIndex": m["endRowIndex"],
                        "startColumnIndex": m["startColumnIndex"],
                        "endColumnIndex": m["endColumnIndex"]
                    }
                }
            })
    requests.append({
        "mergeCells": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": target_range["startRowIndex"],
                "endRowIndex": target_range["endRowIndex"],
                "startColumnIndex": target_range["startColumnIndex"],
                "endColumnIndex": target_range["endColumnIndex"]
            },
            "mergeType": "MERGE_ALL"
        }
    })
    body = {"requests": requests}
    worksheet.spreadsheet.batch_update(body)

def update_google_sheet_user_layout(data, credentials_path, spreadsheet_name, worksheet_name):
    """
    Appends new order rows to the sheet with the following layout:
      - Column A: Serial number (automatically computed, repeated on each row)
      - Column B: Computed "Order From" (e.g., "ES-Esteshari Snoonu")
      - Column C: Order ID
      - Column D: Customer Number
      - Column E: Item description ("quantity - item_name")
      - Column F: Selling Price
    
    Steps:
      1. Find the first empty cell in column A by checking a fixed range (A4:A1000).
      2. Compute the next serial number by scanning that fixed range for numbers.
      3. For each item in data["items"], insert a new row at the bottom.
      4. Order-level fields are repeated on every row.
    
    Returns a dictionary with details about the updated rows.
    """
    # Authenticate with Google Sheets.
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_file(credentials_path, scopes=scope)
    client = gspread.authorize(creds)
    
    try:
        spreadsheet = client.open(spreadsheet_name)
    except Exception as e:
        raise Exception(f"Could not open spreadsheet '{spreadsheet_name}': {e}")
    
    try:
        worksheet = spreadsheet.worksheet(worksheet_name)
    except Exception as e:
        raise Exception(f"Could not open worksheet '{worksheet_name}' in '{spreadsheet_name}': {e}")
    
    # Use a fixed range to check column A (e.g., A4:A1000)
    fixed_range = worksheet.get_values("A4:A1000")
    # fixed_range is a list of lists; each sublist is a row.
    start_row = None
    for index, row in enumerate(fixed_range, start=4):
        # row is a list of values in that row; if empty, then this is our start row.
        if not row or not row[0].strip():
            start_row = index
            break
    if start_row is None:
        # If no empty cell found in A4:A1000, append after that range.
        start_row = 1001

    # Compute the next serial number by scanning the fixed range for numeric values.
    max_sl = 0
    for row in fixed_range:
        try:
            num = int(row[0].strip())
            if num > max_sl:
                max_sl = num
        except (ValueError, IndexError):
            continue
    next_sl = max_sl + 1

    # Prepare items list.
    if "items" in data and isinstance(data["items"], list) and data["items"]:
        items = data["items"]
    else:
        items = [{
            "quantity": data.get("quantity", ""),
            "item_name": data.get("item_name", ""),
            "selling_price": data.get("selling_price", "")
        }]
    num_items = len(items)

    # Append rows at the bottom, one per item.
    rows_used = []
    for idx, item in enumerate(items):
        row_num = start_row + idx
        row_data = [
            str(next_sl),
            data.get("order_type", ""),
            data.get("order_number", ""),
            data.get("customer_phone", ""),
            f"{item.get('quantity', '')} - {item.get('item_name', '')}".strip(" -"),
            item.get("selling_price", "")
        ]
        worksheet.insert_row(row_data, row_num)
        rows_used.append(row_num)

    return {
        "start_row": start_row,
        "next_sl": next_sl,
        "rows_used": rows_used
    }

