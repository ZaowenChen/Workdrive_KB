import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

ACCOUNTS = os.getenv("ZOHO_ACCOUNTS_HOST", "https://accounts.zoho.com")
CLIENT_ID = os.getenv("ZOHO_OAUTH_CLIENT_ID")
CLIENT_SECRET = os.getenv("ZOHO_OAUTH_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("ZOHO_REFRESH_TOKEN")
SCOPES = os.getenv("ZOHO_SCOPES", "")
TOKEN_CACHE = Path(os.getenv("TOKEN_CACHE", "token.json"))


def _save(token: dict) -> None:
    TOKEN_CACHE.write_text(json.dumps(token, indent=2))


def _load() -> dict:
    if TOKEN_CACHE.exists():
        return json.loads(TOKEN_CACHE.read_text())
    return {}


def _refresh() -> dict:
    url = f"{ACCOUNTS}/oauth/v2/token"
    params = {
        "refresh_token": REFRESH_TOKEN,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token",
    }
    response = requests.post(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    token = {
        "access_token": data["access_token"],
        "expires_at": time.time() + int(data.get("expires_in", 3600)) - 60,
    }
    _save(token)
    return token


def get_access_token() -> str:
    token = _load()
    if not token or time.time() >= token.get("expires_at", 0):
        token = _refresh()
    return token["access_token"]


def token_status() -> dict:
    token = _load()
    return {
        "cached": bool(token),
        "expires_in": (token.get("expires_at", 0) - time.time()) if token else None,
    }
