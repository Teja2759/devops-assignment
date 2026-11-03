from io import BytesIO

from pypdf import PdfReader


def extract_pages(data: bytes) -> list[dict]:
    """Return one {"page": n, "text": str} entry per PDF page (1-indexed)."""
    reader = PdfReader(BytesIO(data))
    return [
        {"page": i, "text": (p.extract_text() or "").strip()}
        for i, p in enumerate(reader.pages, start=1)
    ]
