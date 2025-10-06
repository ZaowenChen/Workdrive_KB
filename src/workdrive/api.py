import os
from typing import Any, Dict

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from .auth import get_access_token

API_BASE = os.getenv("WORKDRIVE_API_BASE", "https://workdrive.zoho.com/api/v1")


def _headers() -> Dict[str, str]:
    return {"Authorization": f"Zoho-oauthtoken {get_access_token()}"}


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
    # Use the download endpoint instead of files/{id}/content to avoid the
    # "URL Rule is not configured" error raised on custom domains.
    url = f"{API_BASE}/download/{file_id}"
    response = requests.get(url, headers=_headers(), timeout=120)
    if not response.ok:
        try:
            detail = response.json()
        except ValueError:
            detail = response.text[:200]
        raise RuntimeError(
            f"Failed to download file {file_id}: {response.status_code} {detail}"
        )
    return response.content
