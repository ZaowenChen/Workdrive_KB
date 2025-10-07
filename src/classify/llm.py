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

    enum_fields = list(candidates.keys())
    required_keys = [
        "doc_type",
        "product_line",
        "model",
        "software_version",
        "software_version_other",
        "hardware_version",
        "hardware_version_other",
        "subsystem",
        "audience",
        "priority",
        "lifecycle",
        "confidentiality",
        "keywords",
    ]
    fields_str = ", ".join(enum_fields)
    system_prompt = (
        "You are a meticulous technical librarian. "
        "Classify the document using the provided candidate_values. "
        f"For each enumerated field ({fields_str}) choose exactly one value from candidate_values. "
        "Return strict JSON with all keys: "
        "doc_type, product_line, model, software_version, software_version_other, "
        "hardware_version, hardware_version_other, subsystem, audience, priority, "
        "lifecycle, confidentiality, keywords. "
        "Use an empty string for *_other fields when not needed. "
        "If you answer 'Other' for software_version or hardware_version you must provide the corresponding *_other value (<=64 chars). "
        "If doc_type is 'Other' you must supply non-empty keywords (comma-separated). "
        "Do not invent values outside candidate lists."
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
        parsed = json.loads(content)
        for key in required_keys:
            parsed.setdefault(key, "")
        return parsed
    except json.JSONDecodeError:
        return {}


def run_llm_pass() -> None:
    settings = load_settings()
    candidates = settings["classification"]["candidate_values"]
    required_keys = [
        "doc_type",
        "product_line",
        "model",
        "software_version",
        "software_version_other",
        "hardware_version",
        "hardware_version_other",
        "subsystem",
        "audience",
        "priority",
        "lifecycle",
        "confidentiality",
        "keywords",
    ]
    for document in iter_needs_llm():
        output = _call_llm(document["name"], document.get("excerpt", ""), candidates) or {}
        if output:
            for key in required_keys:
                output.setdefault(key, "")
            upsert_labels(document["file_id"], output, source="llm", confidence=0.9, needs_review=1)
