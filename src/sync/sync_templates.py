import json

from src.db import iter_for_sync, save_audit_change
from src.utils import ensure_template, load_settings
from src.workdrive.datatemplates import update_values


def push_to_workdrive() -> None:
    settings = load_settings()
    template_id = ensure_template(settings)
    for row in iter_for_sync():
        payload = {
            "Document Type": row["doc_type"],
            "Robot Model": row["model_type"],
            "Subsystem": row["subsystem"],
            "Language": row["language"],
        }
        update_values(row["file_id"], template_id, payload)
        save_audit_change(row["file_id"], "sync", "", json.dumps(payload), actor="pipeline")
