import json
import os
from typing import Dict

from src.db import iter_needs_llm, upsert_labels
from src.utils import load_settings


def _call_llm(filename: str, excerpt: str, candidates: Dict[str, list]) -> Dict[str, str]:
    if os.getenv("ENABLE_LLM", "false").lower() != "true":
        return {}

    try:
        from openai import OpenAI
    except ImportError:  # library not installed
        return {}

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {}

    client = OpenAI(api_key=api_key)
    settings = load_settings()
    llm_settings = settings["classification"]["llm"]

    system_prompt = (
        "You classify documents. Given a filename and excerpt, choose exactly one value "
        "for each field (doc_type, model_type, subsystem, language) using only candidate_values. "
        "Return strict JSON with those keys."
    )
    user_prompt = (
        f"Filename: {filename}\n\nExcerpt:\n\"\"\"\n{excerpt[:5000]}\n\"\"\"\n\n"
        f"candidate_values:\n{json.dumps(candidates)}"
    )

    response = client.chat.completions.create(
        model=llm_settings["model"],
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=llm_settings.get("temperature", 0),
        max_tokens=llm_settings.get("max_tokens", 120),
    )

    content = None
    if response.choices:
        message = response.choices[0].message
        if message:
            content = getattr(message, "content", None)

    if not content:
        return {}

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {}


def run_llm_pass() -> None:
    settings = load_settings()
    candidates = settings["classification"]["candidate_values"]
    for document in iter_needs_llm():
        output = _call_llm(document["name"], document.get("excerpt", ""), candidates) or {}
        if output:
            upsert_labels(document["file_id"], output, source="llm", confidence=0.9, needs_review=1)
