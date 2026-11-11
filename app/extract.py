from __future__ import annotations

import io
from pathlib import Path

MAX_UPLOAD_BYTES = 2 * 1024 * 1024
ALLOWED_SUFFIXES = {".txt", ".md", ".docx", ".pdf"}


class ExtractionError(ValueError):
    pass


def extract_text(filename: str, data: bytes, content_type: str | None = None) -> str:
    if len(data) > MAX_UPLOAD_BYTES:
        raise ExtractionError("File is larger than the 2 MB upload limit.")
    if not data:
        raise ExtractionError("The uploaded file is empty.")

    suffix = Path(filename or "").suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        if content_type and content_type.startswith("text/"):
            suffix = ".txt"
        else:
            raise ExtractionError(
                "Unsupported file type. Please upload a .txt, .docx, or .pdf file."
            )

    if suffix in {".txt", ".md"}:
        return _from_text(data)
    if suffix == ".docx":
        return _from_docx(data)
    if suffix == ".pdf":
        return _from_pdf(data)
    raise ExtractionError("Unsupported file type.")


def _from_text(data: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1251", "latin-1"):
        try:
            text = data.decode(encoding)
            break
        except UnicodeDecodeError:
            text = None
    if text is None:
        text = data.decode("utf-8", errors="replace")
    cleaned = text.strip()
    if not cleaned:
        raise ExtractionError("The text file does not contain any readable content.")
    return cleaned


def _from_docx(data: bytes) -> str:
    try:
        from docx import Document
    except ImportError as exc:
        raise ExtractionError("python-docx is not installed.") from exc
    try:
        document = Document(io.BytesIO(data))
    except Exception as exc:
        raise ExtractionError("Could not read the .docx file.") from exc
    parts: list[str] = []
    for paragraph in document.paragraphs:
        if paragraph.text.strip():
            parts.append(paragraph.text.strip())
    for table in document.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if cells:
                parts.append(" | ".join(cells))
    text = "\n".join(parts).strip()
    if not text:
        raise ExtractionError("The Word document does not contain any readable text.")
    return text


def _from_pdf(data: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise ExtractionError("pypdf is not installed.") from exc
    try:
        reader = PdfReader(io.BytesIO(data))
    except Exception as exc:
        raise ExtractionError("Could not read the PDF file.") from exc
    pages: list[str] = []
    for page in reader.pages:
        extracted = page.extract_text() or ""
        if extracted.strip():
            pages.append(extracted.strip())
    text = "\n\n".join(pages).strip()
    if not text:
        raise ExtractionError(
            "No text could be extracted from the PDF. Try a .txt file or paste the text."
        )
    return text
