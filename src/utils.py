import os
import json
import csv
import yaml
from pathlib import Path
from typing import Dict, List

from src.db import all_for_csv, update_from_csv_row
from src.labels import taxonomy
from src.workdrive.datatemplates import create_template_if_missing


def load_settings() -> Dict:
    return yaml.safe_load(open("config/settings.yaml"))


def read_settings() -> Dict:
    # Backward-compatible wrapper around load_settings.
    return load_settings()


def write_csv(path: str):
    rows = all_for_csv()
    if not rows:
        return
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def import_corrected_csv(path: str):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            update_from_csv_row(row)


def _expand_field_options(field: Dict) -> Dict:
    field = dict(field)
    source = field.pop("options_from", None)
    if source:
        if source == "doc_type":
            options = taxonomy.doc_types()
        elif source == "product_line":
            options = taxonomy.product_lines()
        elif source == "model":
            options = taxonomy.all_models()
        elif source == "software_version":
            options = taxonomy.software_options()
        elif source == "hardware_version":
            options = taxonomy.hardware_options()
        elif source == "subsystem":
            options = taxonomy.subsystem_options()
        elif source == "audience":
            options = taxonomy.audience_options()
        elif source == "priority":
            options = taxonomy.priority_options()
        elif source == "lifecycle":
            options = taxonomy.lifecycle_options()
        elif source == "confidentiality":
            options = taxonomy.confidentiality_options()
        else:
            options = []
        field["options"] = options
    return field


def ensure_template(settings: Dict) -> str:
    # In a real system you'd persist the returned template id;
    # here we create once and store id in a local file.
    meta = Path(".template.json")
    if meta.exists():
        return json.loads(meta.read_text())["id"]

    fields = [_expand_field_options(field) for field in settings["template"]["fields"]]
    template = create_template_if_missing(
        settings["template"]["name"],
        settings["template"]["description"],
        fields,
    )
    template_id = template.get("data", {}).get("id") or template.get("id", "")
    meta.write_text(json.dumps({"id": template_id}, indent=2))
    return template_id
