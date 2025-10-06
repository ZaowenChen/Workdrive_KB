import re

import yaml

from src.db import iter_documents_for_heuristics, upsert_labels

REGEX_PATH = "config/regex.yml"


def _match_first(patterns, text):
    for label, pattern in patterns.items():
        if re.search(pattern, text, re.IGNORECASE):
            return label
    return ""


def run_heuristics() -> None:
    config = yaml.safe_load(open(REGEX_PATH))
    for document in iter_documents_for_heuristics():
        text = f"{document['name']} {document.get('excerpt', '')}"
        doc_type = _match_first(config.get("doc_type", {}), text)
        model_type = _match_first(config.get("model_type", {}), text)
        labels = dict(doc_type=doc_type, model_type=model_type, subsystem="", language="")
        upsert_labels(document["file_id"], labels, source="heuristic", confidence=0.6, needs_review=1)
