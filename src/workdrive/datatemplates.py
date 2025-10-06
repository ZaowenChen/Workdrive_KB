from typing import Dict

from .api import get, patch, post


def create_template_if_missing(name: str, description: str, fields: list) -> Dict:
    payload = {"name": name, "description": description, "fields": fields}
    return post("/data/templates", json=payload)


def attach_template(file_id: str, template_id: str):
    return post(f"/files/{file_id}/data/templates", json={"template_id": template_id})


def update_values(file_id: str, template_id: str, values: Dict[str, str]):
    fields = [
        {"label": label, "value": value}
        for label, value in values.items()
        if value is not None and value != ""
    ]
    if not fields:
        return
    return patch(f"/files/{file_id}/data/templates/{template_id}", json={"fields": fields})
