import io
from typing import BinaryIO

from pypdf import PdfReader

from app.exceptions import PDFExtractionError


def extract_text_from_pdf(pdf_file: BinaryIO) -> str:
    try:
        reader = PdfReader(pdf_file)
        text_parts = []

        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)

        full_text = "\n".join(text_parts)
        return full_text.strip()

    except Exception as e:
        raise PDFExtractionError(f"Failed to extract text from PDF: {str(e)}") from e


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 150) -> list[str]:
    if not text:
        return []

    # Validate parameters to prevent infinite loop
    if chunk_size <= 0:
        raise PDFExtractionError(f"chunk_size must be positive, got {chunk_size}")

    if overlap < 0:
        raise PDFExtractionError(f"overlap cannot be negative, got {overlap}")

    if overlap >= chunk_size:
        raise PDFExtractionError(
            f"overlap ({overlap}) must be less than chunk_size ({chunk_size})"
        )

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap

    return chunks


def extract_and_chunk_pdf(pdf_file: BinaryIO, chunk_size: int = 1000, overlap: int = 150) -> list[str]:
    text = extract_text_from_pdf(pdf_file)
    return chunk_text(text, chunk_size, overlap)
