import hashlib
import io
import os

import pandas as pd
from docx import Document
from pdfminer.high_level import extract_text as pdf_extract_text

try:
    from pptx import Presentation  # optional: pip install python-pptx
except ImportError:
    Presentation = None

from src.db import iter_documents_without_excerpt, store_excerpt
from src.workdrive.api import download_file_bytes

EXCERPT_MAX = int(os.getenv("EXCERPT_MAX_CHARS", "15000"))
EXCERPT_PDF_MAX_PAGES = int(os.getenv("EXCERPT_PDF_MAX_PAGES", "0"))

def _extract_content(data: bytes, suffix: str) -> str:
    buffer = io.BytesIO(data)
    extension = (suffix or "").lower()
    try:
        if extension == ".pdf":
            pdf_kwargs = {}
            if EXCERPT_PDF_MAX_PAGES > 0:
                pdf_kwargs["maxpages"] = EXCERPT_PDF_MAX_PAGES
            text = pdf_extract_text(buffer, **pdf_kwargs) or ""
            return text[:EXCERPT_MAX]

        if extension == ".docx":
            document = Document(buffer)
            text = "\n".join(p.text for p in document.paragraphs)
            return text[:EXCERPT_MAX]

        if extension == ".xlsx":
            df = pd.read_excel(buffer, sheet_name=0, nrows=20, engine="openpyxl")
            return df.to_csv(sep=" ", index=False)[:EXCERPT_MAX]

        if extension == ".xls":
            # Requires a reader that supports xls; install xlrd==1.2.0 or a compatible engine
            df = pd.read_excel(buffer, sheet_name=0, nrows=20)
            return df.to_csv(sep=" ", index=False)[:EXCERPT_MAX]

        if extension == ".pptx":
            if Presentation is None:
                return ""
            presentation = Presentation(buffer)
            text_runs = []
            for slide in presentation.slides:
                for shape in getattr(slide, "shapes", []):
                    text = getattr(shape, "text", "")
                    if text:
                        text_runs.append(text)
            return "\n".join(text_runs)[:EXCERPT_MAX]

        # (optional) else: unknown extension -> empty
    except Exception:
        return ""  # swallow parse errors per your design

    return ""

def run_extraction() -> None:
    for document in iter_documents_without_excerpt():
        # IMPORTANT: pass the correct id that your download function expects
        rid = document.get("resource_id") or document.get("file_id")
        content = download_file_bytes(rid)
        excerpt = _extract_content(content, document.get("suffix", ".pdf"))
        sha256 = hashlib.sha256(content).hexdigest()
        store_excerpt(rid, excerpt, sha256)

