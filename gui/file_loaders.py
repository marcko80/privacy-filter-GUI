"""File loaders for Privacy Filter GUI.

Supporta formati testuali e, se le librerie opzionali sono installate,
anche PDF (pypdf) e DOCX (python-docx).
"""

from __future__ import annotations

import io
from typing import Tuple

TEXT_EXTS = {"txt", "csv", "json", "log", "md", "xml", "html", "yaml", "yml"}
BINARY_EXTS = {"pdf", "docx"}
ALL_EXTS = sorted(TEXT_EXTS | BINARY_EXTS)


def _decode(raw: bytes) -> str:
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore")


def _load_pdf(raw: bytes) -> str:
    try:
        from pypdf import PdfReader
    except Exception as exc:
        raise RuntimeError(
            "pypdf non installato. Esegui: pip install pypdf"
        ) from exc
    reader = PdfReader(io.BytesIO(raw))
    parts = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or "")
        except Exception:
            parts.append("")
    return "\n\n".join(parts)


def _load_docx(raw: bytes) -> str:
    try:
        import docx
    except Exception as exc:
        raise RuntimeError(
            "python-docx non installato. Esegui: pip install python-docx"
        ) from exc
    doc = docx.Document(io.BytesIO(raw))
    return "\n".join(p.text for p in doc.paragraphs)


def load_file(filename: str, raw: bytes) -> Tuple[str, str]:
    """Return (text, detected_ext)."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "txt"
    if ext == "pdf":
        return _load_pdf(raw), ext
    if ext == "docx":
        return _load_docx(raw), ext
    return _decode(raw), ext
