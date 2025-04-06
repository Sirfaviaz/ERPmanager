from .snoonu_extractor import extract_snoonu_details
from .rafeeq_extractor import extract_rafeeq_details
import PyPDF2
from typing import Union
from io import BytesIO
from datetime import datetime


def get_file_reader(pdf_input: Union[str, BytesIO]):
    """
    Accepts file path or Django InMemoryUploadedFile and returns file-like object.
    """
    if isinstance(pdf_input, str):
        return open(pdf_input, 'rb')
    elif hasattr(pdf_input, 'read'):
        return pdf_input
    else:
        raise ValueError("Unsupported file input")


def read_pdf_text(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


def determine_bill_type(file):
    file.seek(0)
    text = read_pdf_text(file)
    file.seek(0)
    return "rafeeq" if "vendor" in text.lower() else "snoonu"


def extract_order_data(file):
    bill_type = determine_bill_type(file)
    if bill_type == "rafeeq":
        return extract_rafeeq_details(file), "rafeeq"
    else:
        return extract_snoonu_details(file), "snoonu"


def parse_flexible_date(date_str):
    """Try parsing a date string using multiple common formats."""
    date_formats = [
        "%B %d, %Y",     # April 3, 2025
        "%b %d, %Y",     # Apr 3, 2025
        "%b. %d, %Y",    # Jan. 27, 2025
        "%d/%m/%Y",      # 03/04/2025
        "%m/%d/%Y",      # 04/03/2025
        "%Y-%m-%d",      # 2025-04-03
    ]
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue
    return None
