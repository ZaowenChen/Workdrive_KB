import functools
from pathlib import Path
from typing import Dict, List

import yaml


_TAXONOMY_PATH = Path("config/taxonomy.yaml")


@functools.lru_cache(maxsize=1)
def load_taxonomy() -> Dict:
    data = yaml.safe_load(_TAXONOMY_PATH.read_text(encoding="utf-8"))
    return data


def doc_types() -> List[str]:
    return load_taxonomy()["doc_type"]


def product_lines() -> List[str]:
    return load_taxonomy()["product_line"]


def models_for(product_line: str) -> List[str]:
    models = load_taxonomy()["model"]
    return models.get(product_line, models.get("default", []))


def software_series() -> Dict[str, List[str]]:
    return load_taxonomy().get("software_version", {}).get("series", {})


def software_options(include_series: bool = True) -> List[str]:
    taxonomy = load_taxonomy()
    series = taxonomy.get("software_version", {}).get("series", {})
    generic = series.get("generic", [])
    values: List[str] = []
    if include_series:
        for name, options in series.items():
            if name == "generic":
                continue
            values.extend(options)
    values.extend(generic)
    if taxonomy.get("software_version", {}).get("allow_other", False):
        values.append("Other")
    return values


def software_allows_other() -> bool:
    return bool(load_taxonomy().get("software_version", {}).get("allow_other", False))


def all_models() -> List[str]:
    seen: List[str] = []
    for line in product_lines():
        for model in models_for(line):
            if model not in seen:
                seen.append(model)
    return seen


def _hardware_config() -> Dict:
    config = load_taxonomy().get("hardware_version", {})
    return config or {}


def hardware_options_for_model(model: str | None) -> List[str]:
    config = _hardware_config()
    options: List[str] = []
    model_specific = config.get("model_specific", {})
    if model and model in model_specific:
        options.extend(model_specific[model])
    for key in ("options", "global"):
        for value in config.get(key, []) or []:
            if value not in options:
                options.append(value)
    if config.get("allow_other_text", False) and "Other" not in options:
        options.append("Other")
    return options


def hardware_options() -> List[str]:
    return hardware_options_for_model(None)


def hardware_allows_other() -> bool:
    return _hardware_config().get("allow_other_text", False)


def subsystem_options() -> List[str]:
    return load_taxonomy()["subsystem"]


def audience_options() -> List[str]:
    return load_taxonomy()["audience"]


def priority_options() -> List[str]:
    return load_taxonomy()["priority"]


def lifecycle_options() -> List[str]:
    return load_taxonomy()["lifecycle"]


def confidentiality_options() -> List[str]:
    return load_taxonomy()["confidentiality"]
