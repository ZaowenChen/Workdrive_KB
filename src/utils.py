import os
import json
import csv
import yaml
from pathlib import Path
from typing import Dict, List
from src.db import all_for_csv, update_from_csv_row
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


def ensure_template(settings: Dict) -> str:
    # In a real system you'd persist the returned template id;
    # here we create once and store id in a local file.
    meta = Path(".template.json")
    if meta.exists():
        return json.loads(meta.read_text())["id"]
    template = create_template_if_missing(settings["template"]["name"],
                                          settings["template"]["description"],
                                          settings["template"]["fields"])
    template_id = template.get("data", {}).get("id") or template.get("id", "")
    meta.write_text(json.dumps({"id": template_id}, indent=2))
    return template_id
