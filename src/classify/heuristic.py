import re

import yaml

from src.db import iter_documents_for_heuristics, upsert_labels
from src.labels import taxonomy

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
        product_line = _match_first(config.get("product_line", {}), text)
        model = _match_first(config.get("model", {}), text)
        subsystem = _match_first(config.get("subsystem", {}), text)

        if model and not product_line:
            for candidate_line in taxonomy.product_lines():
                if model in taxonomy.models_for(candidate_line):
                    product_line = candidate_line
                    break

        labels = dict(
            doc_type=doc_type,
            product_line=product_line,
            model=model,
            software_version="",
            software_version_other="",
            hardware_version="",
            hardware_version_other="",
            subsystem=subsystem,
            audience="",
            priority="",
            lifecycle="",
            confidentiality="",
            keywords="",
        )
        upsert_labels(document["file_id"], labels, source="heuristic", confidence=0.6, needs_review=1)
