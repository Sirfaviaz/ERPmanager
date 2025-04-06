import PyPDF2
import re
from datetime import datetime
from .filetools import get_file_reader


def extract_all_text(pdf_input):
    """Extract all text from a PDF file path or file-like object."""
    f = get_file_reader(pdf_input)
    reader = PyPDF2.PdfReader(f)
    full_text = ""
    for page in reader.pages:
        page_text = page.extract_text() or ""
        full_text += page_text + "\n"
    if hasattr(f, 'seek'):
        f.seek(0)
    if isinstance(pdf_input, str):
        f.close()
    return full_text


def extract_rafeeq_details(pdf_input):
    full_text = extract_all_text(pdf_input)
    lines = [line.strip() for line in full_text.splitlines() if line.strip()]

    # --- Extract Order For ---
    order_for = ""
    for line in lines:
        if "vendor" in line.lower():
            parts = line.split(":")
            if len(parts) > 1:
                order_for = parts[1].strip()
                if order_for.startswith(")"):
                    order_for = order_for[1:].strip()
            break

    # --- Extract Order Number ---
    order_number = ""
    for line in lines:
        lower_line = line.lower().replace(" ", "")
        if "prepaid" in lower_line or "cashondelivery" in lower_line or "ordernumber" in lower_line:
            match = re.search(r"(\d+)", line)
            if match:
                order_number = match.group(1)
                break
    if not order_number:
        for line in lines:
            match = re.search(r"\b(\d{7,8})\b", line)
            if match:
                order_number = match.group(1)
                break

    # --- Extract Customer Phone ---
    customer_phone = ""
    phone_pattern = re.compile(r"[\+\d][\d\-\s\(\)]+")
    for i, line in enumerate(lines):
        if "mobile number" in line.lower():
            match = phone_pattern.search(line)
            if match:
                customer_phone = match.group().strip()
            else:
                for j in range(i + 1, len(lines)):
                    if any(ch.isdigit() for ch in lines[j]):
                        m = phone_pattern.search(lines[j])
                        if m:
                            customer_phone = m.group().strip()
                        else:
                            customer_phone = lines[j].strip()
                        break
            if customer_phone:
                break

    # --- Extract Customer Name ---
    customer_name = ""
    for line in lines:
        if "customer" in line.lower():
            if ":" in line:
                customer_name = line.split(":")[-1].strip()
            elif ")" in line:
                customer_name = line.split(")")[-1].strip()
            break

    # --- Extract Order Date ---
    order_date = None
    for line in lines:
        try:
            order_date = datetime.strptime(line.strip(), "%b %d, %Y %H:%M:%S").date()
            break
        except:
            continue

    # --- Extract Items ---
    items = []
    item_header_index = None
    for i, line in enumerate(lines):
        if "item" in line.lower():
            item_header_index = i
            break

    if item_header_index is not None:
        i = item_header_index + 1
        candidate_buffer = []
        while i < len(lines):
            if any(term in lines[i].lower() for term in ["subtotal", "delivery fee", "total amount", "thank you"]):
                break
            if "promotion" in lines[i].lower():
                i += 1
                continue
            tokens = lines[i].split()
            if len(tokens) >= 2 and re.fullmatch(r"\d+", tokens[0]):
                try:
                    qty_val = int(tokens[0])
                except:
                    qty_val = 0
                if qty_val <= 10:
                    quantity = tokens[0]
                    price_match = re.search(r"(\d+(\.\d+)?)", tokens[1])
                    selling_price = price_match.group(1) if price_match else ""
                    item_name = " ".join(candidate_buffer).strip() if candidate_buffer else ""
                    items.append({
                        "quantity": quantity,
                        "item_name": item_name,
                        "selling_price": selling_price
                    })
                    candidate_buffer = []
                    i += 1
                    continue
            candidate_buffer.append(lines[i])
            i += 1

    if not items:
        items = [{"quantity": "", "item_name": "", "selling_price": ""}]

    return {
        "order_type": "rafeeq",
        "order_for": order_for,
        "order_date": order_date,
        "order_number": order_number,
        "customer_name": customer_name,
        "customer_phone": customer_phone,
        "items": items
    }
