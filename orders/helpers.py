def compute_order_from(order_type, order_for):
    lower_type = order_type.lower().strip()
    lower_for = order_for.lower().strip()
    
    if "golden" in lower_for:
        vendor = "Golden Phones"
    elif "esteshari" in lower_for or "estishari" in lower_for:
        vendor = "Esteshari"
    else:
        vendor = order_for

    if lower_type == "snoonu":
        if vendor == "Golden Phones":
            return "GS-Golden Phones Snoonu"
        elif vendor == "Esteshari":
            return "ES-Esteshari Snoonu"
        else:
            return vendor + " Snoonu"
    elif lower_type == "rafeeq":
        if vendor == "Golden Phones":
            return "GR-Golden Phones Rafeeq"
        elif vendor == "Esteshari":
            return "ER-Esteshari Rafeeq"
        else:
            return vendor + " Rafeeq"
    else:
        return order_for


def try_extract_date_from_lines(lines):
    for line in lines:
        # Format: YYYY-MM-DD
        match = re.search(r'\b(\d{4})[-/](\d{2})[-/](\d{2})\b', line)
        if match:
            try:
                return datetime.date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
            except:
                continue
        # Format: DD-MM-YYYY or DD/MM/YYYY
        match = re.search(r'\b(\d{2})[-/](\d{2})[-/](\d{4})\b', line)
        if match:
            try:
                return datetime.date(int(match.group(3)), int(match.group(2)), int(match.group(1)))
            except:
                continue
    return None