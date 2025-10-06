import os
from typing import Any, Dict

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from .auth import get_access_token

API_BASE = os.getenv("WORKDRIVE_API_BASE", "https://workdrive.zoho.com/api/v1")
APP_BASE = os.getenv("WORKDRIVE_APP_BASE")
ORG_ID = os.getenv("WORKDRIVE_ORG_ID")

if not APP_BASE:
    base = API_BASE.rstrip("/")
    if base.endswith("/api/v1"):
        base = base[: -len("/api/v1")]
    APP_BASE = base


def _headers() -> Dict[str, str]:
    headers = {"Authorization": f"Zoho-oauthtoken {get_access_token()}"}
    if ORG_ID:
        headers["X-ZOHO-WORKDRIVE-ORGID"] = ORG_ID
    return headers


@retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(5))
def get(path: str, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    response = requests.get(
        f"{API_BASE}{path}",
        headers=_headers(),
        params=params or {},
        timeout=60,
    )
    if response.status_code in (429, 500, 502, 503, 504):
        raise RuntimeError(f"Retryable: {response.status_code} {response.text[:200]}")
    response.raise_for_status()
    return response.json()


@retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(5))
def post(path: str, json: Dict[str, Any] | None = None) -> Dict[str, Any]:
    response = requests.post(
        f"{API_BASE}{path}",
        headers={**_headers(), "Content-Type": "application/json"},
        json=json,
        timeout=60,
    )
    if response.status_code in (429, 500, 502, 503, 504):
        raise RuntimeError(f"Retryable: {response.status_code} {response.text[:200]}")
    response.raise_for_status()
    return response.json()


@retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(5))
def patch(path: str, json: Dict[str, Any] | None = None) -> Dict[str, Any]:
    response = requests.patch(
        f"{API_BASE}{path}",
        headers={**_headers(), "Content-Type": "application/json"},
        json=json,
        timeout=60,
    )
    if response.status_code in (429, 500, 502, 503, 504):
        raise RuntimeError(f"Retryable: {response.status_code} {response.text[:200]}")
    response.raise_for_status()
    return response.json()


def download_file_bytes(file_id: str) -> bytes:
    # The download API can differ across deployments; try the newer download
    # endpoint first but fall back to the legacy content endpoint if needed.
    endpoints = (
        f"{API_BASE}/download/{file_id}",
        f"{API_BASE}/files/{file_id}/content",
    )
    errors: list[str] = []
    for url in endpoints:
        response = requests.get(url, headers=_headers(), timeout=120)
        if response.ok:
            return response.content
        try:
            detail = response.json()
        except ValueError:
            detail = response.text[:200]
        errors.append(f"{url}: {response.status_code} {detail}")
        # Only attempt the fallback when it makes sense; keep trying on known
        # mismatches (400/404/422) and bail early on hard failures.
        if response.status_code >= 500:
            break
    raise RuntimeError(f"Failed to download file {file_id}: {'; '.join(errors)}")
