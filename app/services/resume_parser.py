"""
PDF resume text extraction.
"""

import os

import pdfplumber


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract all text from a PDF file.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        Extracted text from all pages, joined by double newlines.

    Raises:
        FileNotFoundError: If the file does not exist.
        Exception: On PDF read errors.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    text_content = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                text_content.append(text)

    return "\n\n".join(text_content)
