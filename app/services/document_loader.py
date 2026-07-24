from pathlib import Path

from pypdf import PdfReader


SUPPORTED_SUFFIXES = {".md", ".markdown", ".txt", ".pdf"}


def is_supported_file(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_SUFFIXES


def load_document_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".md", ".markdown", ".txt"}:
        return path.read_text(encoding="utf-8")
    if suffix == ".pdf":
        return _load_pdf_text(path)
    raise ValueError(f"Unsupported file type: {suffix}")


def _load_pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages)

