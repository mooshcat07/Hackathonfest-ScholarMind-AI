
import pymupdf
from pathlib import Path
import re


def extract_pdf_pages(pdf_path):
    """Extract text from a PDF while preserving page numbers."""

    path = Path(pdf_path).expanduser()

    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    if path.suffix.lower() != ".pdf":
        raise ValueError("Please provide a PDF document.")

    pages = []

    with pymupdf.open(path) as document:

        for page_number, page in enumerate(document, start=1):

            text = page.get_text("text").strip()

            if text:
                pages.append({
                    "page": page_number,
                    "text": text
                })

    if not pages:
        raise ValueError(
            "No text could be extracted. This PDF may contain scanned images."
        )

    return pages


def search_document(query, pages, limit=5):
    """Find the most relevant pages using keyword matching."""

    query_words = set(re.findall(r"\w+", query.lower()))

    if not query_words:
        return []

    results = []

    for page in pages:

        page_text = page["text"]
        page_words = set(re.findall(r"\w+", page_text.lower()))

        score = len(query_words.intersection(page_words))

        if score > 0:
            results.append({
                "page": page["page"],
                "score": score,
                "text": page_text
            })

    results.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return results[:limit]
