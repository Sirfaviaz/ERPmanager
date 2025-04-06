# orders/filetools.py

from typing import Union
from io import BytesIO

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
