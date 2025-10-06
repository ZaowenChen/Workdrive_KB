import hashlib
import io
import os

import pandas as pd
from docx import Document
from pdfminer.high_level import extract_text as pdf_extract_text
from pptx import Presentation

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
            return (pdf_extract_text(buffer, **pdf_kwargs) or "")[:EXCERPT_MAX]
        if extension in (".docx",):
            document = Document(buffer)
            return "\n".join(paragraph.text for paragraph in document.paragraphs)[:EXCERPT_MAX]
        if extension in (".xlsx", ".xls"):
            dataframe = pd.read_excel(buffer, sheet_name=0, nrows=20, engine="openpyxl")
            return dataframe.to_csv(sep=" ", index=False)[:EXCERPT_MAX]
        if extension in (".pptx", ".ppt"):
            presentation = Presentation(buffer)
            text_runs = []
            for slide in presentation.slides:
                for shape in getattr(slide, "shapes", []):
                    text = getattr(shape, "text", "")
                    if text:
                        text_runs.append(text)
            return "\n".join(text_runs)[:EXCERPT_MAX]
    except Exception:
        return ""
    return ""


def run_extraction() -> None:
    for document in iter_documents_without_excerpt():
        content = download_file_bytes(document["file_id"])
        excerpt = _extract_content(content, document.get("suffix", ".pdf"))
        sha256 = hashlib.sha256(content).hexdigest()
        store_excerpt(document["file_id"], excerpt, sha256)
