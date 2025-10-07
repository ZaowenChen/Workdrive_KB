import json

from src.db import iter_for_sync, save_audit_change
from src.utils import ensure_template, load_settings
from src.workdrive.datatemplates import update_values


def push_to_workdrive() -> None:
    settings = load_settings()
    template_id = ensure_template(settings)
    for row in iter_for_sync():
        payload = {
            "Doc Type": row["doc_type"],
            "Product Line": row["product_line"],
            "Model": row["model"],
            "Software Version": row["software_version"],
            "Software Version (Other)": row["software_version_other"],
            "Hardware Version": row["hardware_version"],
            "Hardware Version (Other)": row["hardware_version_other"],
            "Subsystem": row["subsystem"],
            "Audience": row["audience"],
            "Priority": row["priority"],
            "Lifecycle": row["lifecycle"],
            "Confidentiality": row["confidentiality"],
            "Keywords": row["keywords"],
        }
        update_values(row["file_id"], template_id, payload)
        save_audit_change(row["file_id"], "sync", "", json.dumps(payload), actor="pipeline")
