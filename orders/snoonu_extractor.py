import PyPDF2
import re
from datetime import datetime
from .filetools import get_file_reader
from .helpers import try_extract_date_from_lines  # fallback date extractor


def extract_snoonu_details(pdf_input):
    f = get_file_reader(pdf_input)
    reader = PyPDF2.PdfReader(f)
    full_text = ""
    for page in reader.pages:
        full_text += page.extract_text() or ""
        full_text += "\n"

    if hasattr(f, 'seek'):
        f.seek(0)
    if isinstance(pdf_input, str):
        f.close()

    lines = [line.strip() for line in full_text.splitlines() if line.strip()]

    # --- Extract Order For (Usually first line or after "Snoonu Portal") ---
    order_for = ""
    for i, line in enumerate(lines):
        if "snoonu portal" in line.lower() and i + 1 < len(lines):
            order_for = lines[i + 1].strip()
            break
    if not order_for and lines:
        order_for = lines[0]

    # --- Extract Order Date ---
    order_date = None
    for line in lines:
        match = re.search(r"\d{4}-\d{2}-\d{2}", line)
        if match:
            try:
                order_date = datetime.strptime(match.group(0), "%Y-%m-%d").date()
                break
            except:
                continue
    if not order_date:
        order_date = try_extract_date_from_lines(lines)

    # --- Extract Order Number ---
    order_number = ""
    for i, line in enumerate(lines):
        if "order number" in line.lower():
            for j in range(i + 1, len(lines)):
                if lines[j].strip().isdigit():
                    order_number = lines[j].strip()
                    break
            break

    # --- Extract Customer Name ---
    customer_name = ""
    for i, line in enumerate(lines):
        if "customer" in line.lower():
            for j in range(i + 1, len(lines)):
                if any(c.isalpha() for c in lines[j]):
                    customer_name = re.sub(r"[^a-zA-Z\s]", "", lines[j]).strip()
                    break
            break

    # --- Extract Customer Phone ---
    customer_phone = ""
    for i, line in enumerate(lines):
        if "customer phone" in line.lower():
            for j in range(i + 1, len(lines)):
                phone_match = re.search(r"\d{7,}", lines[j])
                if phone_match:
                    customer_phone = phone_match.group()
                    break
            break

    # --- Extract Items ---
    items = []
    i = 0
    while i < len(lines):
        match = re.match(r"^(\d+)\s", lines[i])
        if match:
            quantity = match.group(1)
            item_lines = [lines[i][len(quantity):].strip()]
            j = i + 1
            selling_price = ""
            while j < len(lines):
                if "qr." in lines[j].lower():
                    price_match = re.search(r"qr\.\s*([\d.]+)", lines[j].lower())
                    if price_match:
                        selling_price = price_match.group(1)
                    break
                item_lines.append(lines[j])
                j += 1
            item_name = " ".join(item_lines).strip()
            if quantity and selling_price:
                items.append({
                    "quantity": quantity,
                    "item_name": item_name,
                    "selling_price": selling_price
                })
            i = j + 1
        else:
            i += 1

    if not items:
        items = [{"quantity": "", "item_name": "", "selling_price": ""}]

    return {
        "order_type": "snoonu",
        "order_for": order_for,
        "order_date": order_date,
        "order_number": order_number,
        "customer_name": customer_name,
        "customer_phone": customer_phone,
        "items": items
    }
