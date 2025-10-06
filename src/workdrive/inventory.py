import os
from typing import Dict, Generator

from tqdm import tqdm

from .api import get
from src.db import mark_seen, upsert_document

TEAMFOLDER_ID = os.getenv("TEAMFOLDER_ID")


def _list_items(folder_id: str, limit: int = 50) -> Generator[Dict, None, None]:
    offset = 0
    while True:
        data = get(
            f"/teamfolders/{folder_id}/files",
            params={"page[limit]": limit, "page[offset]": offset, "filter[type]": "all"},
        )
        items = data.get("data", [])
        if not items:
            break
        for item in items:
            yield item
        if len(items) < limit:
            break
        offset += limit


def _recurse(folder_id: str, prefix: str = "") -> Generator[Dict, None, None]:
    for item in _list_items(folder_id):
        attributes = item.get("attributes", {})
        item_id = item.get("id")
        name = attributes.get("name")
        item_type = attributes.get("type")
        full_path = f"{prefix}/{name}" if prefix else name
        if item_type == "folder":
            yield from _recurse(item_id, full_path)
        else:
            yield {
                "file_id": item_id,
                "name": name,
                "path": full_path,
                "size": attributes.get("content_size"),
                "created_time": attributes.get("created_at"),
                "modified_time": attributes.get("modified_at"),
            }


def crawl_incremental() -> None:
    assert TEAMFOLDER_ID, "TEAMFOLDER_ID not set"
    for row in tqdm(_recurse(TEAMFOLDER_ID), desc="Crawling"):
        upsert_document(row)
        mark_seen(row["file_id"])
