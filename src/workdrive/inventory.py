import os
from typing import Dict, Generator, Iterator, Tuple
from urllib.parse import urljoin

from tqdm import tqdm

from .api import get, API_BASE, APP_BASE
from src.db import mark_seen, upsert_document

TEAMFOLDER_ID = os.getenv("TEAMFOLDER_ID")
ROOT_FOLDER_ID = os.getenv("WORKDRIVE_ROOT_FOLDER_ID")
CRAWL_PAGE_LIMIT = int(os.getenv("WORKDRIVE_CRAWL_PAGE_LIMIT", "50"))


def _list_items(container_id: str, container_kind: str, limit: int = CRAWL_PAGE_LIMIT) -> Iterator[Dict]:
    path_prefix = "teamfolders" if container_kind == "teamfolder" else "files"
    offset = 0
    while True:
        data = get(
            f"/{path_prefix}/{container_id}/files",
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


def _recurse(container_id: str, container_kind: str, prefix: str = "") -> Generator[Dict, None, None]:
    for item in _list_items(container_id, container_kind):
        attributes = item.get("attributes", {})
        item_id = item.get("id")
        name = attributes.get("name")
        item_type = attributes.get("type")
        full_path = f"{prefix}/{name}" if prefix else name
        if item_type == "folder":
            yield from _recurse(item_id, "folder", full_path)
        else:
            permalink = attributes.get("permalink") or attributes.get("permalink_url") or attributes.get("web_url")
            if permalink and not permalink.startswith("http"):
                permalink = urljoin(APP_BASE.rstrip("/") + "/", permalink.lstrip("/"))
            if not permalink:
                permalink = f"{APP_BASE.rstrip('/')}/file/{item_id}"
            download_url = attributes.get("download_url") or f"{API_BASE}/download/{item_id}"
            yield {
                "file_id": item_id,
                "name": name,
                "path": full_path,
                "size": attributes.get("content_size"),
                "created_time": attributes.get("created_at"),
                "modified_time": attributes.get("modified_at"),
                "permalink": permalink,
                "download_url": download_url,
            }


def crawl_incremental() -> None:
    seeds: Tuple[Tuple[str, str, str], ...]
    if ROOT_FOLDER_ID:
        try:
            folder_meta = get(f"/files/{ROOT_FOLDER_ID}")
            attributes = folder_meta.get("data", {}).get("attributes", {})
            root_name = attributes.get("name", ROOT_FOLDER_ID)
        except Exception:
            root_name = ROOT_FOLDER_ID
        seeds = ((ROOT_FOLDER_ID, "folder", root_name),)
    else:
        assert TEAMFOLDER_ID, "TEAMFOLDER_ID not set"
        seeds = ((TEAMFOLDER_ID, "teamfolder", ""),)

    for container_id, container_kind, prefix in seeds:
        for row in tqdm(_recurse(container_id, container_kind, prefix), desc="Crawling"):
            upsert_document(row)
            mark_seen(row["file_id"])
