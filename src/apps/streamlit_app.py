import math

import pandas as pd
import streamlit as st

from src.db import all_for_csv, update_from_csv_row
from src.labels import taxonomy

st.set_page_config(page_title="Cobotiq Knowledge Labeling", layout="wide")
st.title("Cobotiq Knowledge Labeling")

rows = all_for_csv()
dataframe = pd.DataFrame(rows).fillna("")

if dataframe.empty:
    st.info("No data yet. Run crawl/extract/classify first.")
    st.stop()

st.caption(
    "Review extracted documents, enforce required metadata, and click **Save Row** to persist changes. "
    "Fields marked with *Other* expose an additional free-text box that is required when selected."
)


def _clean(value):
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return str(value).strip()


def _options_with_blank(options):
    ordered = []
    for option in options:
        if option not in ordered:
            ordered.append(option)
    return [""] + ordered


def _safe_index(options, value, fallback=""):
    candidate = value
    if isinstance(candidate, str):
        candidate = candidate.strip()
    elif candidate is None:
        candidate = ""
    else:
        candidate = str(candidate)
    if not candidate and fallback:
        candidate = fallback
    if candidate in options:
        return options.index(candidate)
    if fallback and fallback in options:
        return options.index(fallback)
    return 0


def _model_options(product_line: str):
    if product_line:
        options = taxonomy.models_for(product_line)
    else:
        options = taxonomy.all_models()
    if "Other" not in options:
        options.append("Other")
    return options


doc_type_options = taxonomy.doc_types()
product_line_options = taxonomy.product_lines()
subsystem_options = taxonomy.subsystem_options()
audience_options = taxonomy.audience_options()
priority_options = taxonomy.priority_options()
lifecycle_options = taxonomy.lifecycle_options()
confidentiality_options = taxonomy.confidentiality_options()
software_option_list = taxonomy.software_options()


for index, row in dataframe.iterrows():
    with st.expander(row["path"], expanded=False):
        top_col, meta_col = st.columns([2, 1])
        with top_col:
            st.write(row["name"])
            st.caption(row["path"])
            links = []
            permalink = _clean(row.get("permalink"))
            download_url = _clean(row.get("download_url"))
            if permalink:
                links.append(f"[Open]({permalink})")
            if download_url:
                links.append(f"[Download]({download_url})")
            if links:
                st.markdown(" • ".join(links))
        with meta_col:
            st.metric("Size (bytes)", _clean(row.get("size")) or "—")
            st.metric("Last Modified", _clean(row.get("modified_time")) or "—")

        doc_type = st.selectbox(
            "Doc Type",
            _options_with_blank(doc_type_options),
            index=_safe_index(_options_with_blank(doc_type_options), _clean(row.get("doc_type"))),
            key=f"doc_type_{row['file_id']}",
        )

        product_line = st.selectbox(
            "Product Line",
            _options_with_blank(product_line_options),
            index=_safe_index(_options_with_blank(product_line_options), _clean(row.get("product_line"))),
            key=f"product_line_{row['file_id']}",
        )

        model_choices = _options_with_blank(_model_options(product_line))
        model = st.selectbox(
            "Model",
            model_choices,
            index=_safe_index(model_choices, _clean(row.get("model"))),
            key=f"model_{row['file_id']}",
        )

        software_choices = _options_with_blank(software_option_list)
        software_version = st.selectbox(
            "Software Version",
            software_choices,
            index=_safe_index(software_choices, _clean(row.get("software_version"))),
            key=f"software_{row['file_id']}",
        )
        software_other_required = software_version == "Other"
        software_other_label = "Software Version (Other)" + (" *" if software_other_required else "")
        software_version_other = st.text_input(
            software_other_label,
            _clean(row.get("software_version_other")),
            key=f"software_other_{row['file_id']}",
            disabled=not software_other_required,
        ) if software_other_required or _clean(row.get("software_version_other")) else ""

        hw_options_list = taxonomy.hardware_options_for_model(model if model else None)
        if not hw_options_list:
            hw_options_list = taxonomy.hardware_options()
        hardware_choices = _options_with_blank(hw_options_list)
        hardware_version = st.selectbox(
            "Hardware Version",
            hardware_choices,
            index=_safe_index(hardware_choices, _clean(row.get("hardware_version")), fallback="Other"),
            key=f"hardware_{row['file_id']}",
        )
        hardware_other_required = hardware_version == "Other"
        hardware_other_label = "Hardware Version (Other)" + (" *" if hardware_other_required else "")
        hw_other_initial = _clean(row.get("hardware_version_other"))
        if hardware_other_required and not hw_other_initial:
            hw_other_initial = "Unknown"
        hardware_version_other = st.text_input(
            hardware_other_label,
            hw_other_initial,
            key=f"hardware_other_{row['file_id']}",
            disabled=not hardware_other_required,
        )
        if not hardware_other_required:
            hardware_version_other = _clean(row.get("hardware_version_other"))

        subsystem = st.selectbox(
            "Subsystem",
            _options_with_blank(subsystem_options),
            index=_safe_index(_options_with_blank(subsystem_options), _clean(row.get("subsystem"))),
            key=f"subsystem_{row['file_id']}",
        )

        audience = st.selectbox(
            "Audience",
            _options_with_blank(audience_options),
            index=_safe_index(_options_with_blank(audience_options), _clean(row.get("audience"))),
            key=f"audience_{row['file_id']}",
        )

        priority = st.selectbox(
            "Priority",
            priority_options,
            index=_safe_index(priority_options, _clean(row.get("priority")), fallback="Medium"),
            key=f"priority_{row['file_id']}",
        )

        lifecycle = st.selectbox(
            "Lifecycle",
            lifecycle_options,
            index=_safe_index(lifecycle_options, _clean(row.get("lifecycle")), fallback="Active"),
            key=f"lifecycle_{row['file_id']}",
        )

        confidentiality = st.selectbox(
            "Confidentiality",
            confidentiality_options,
            index=_safe_index(confidentiality_options, _clean(row.get("confidentiality")), fallback="Internal"),
            key=f"confidentiality_{row['file_id']}",
        )

        keywords_label = "Keywords (comma separated)" + (" *" if doc_type == "Other" else "")
        keywords = st.text_input(
            keywords_label,
            _clean(row.get("keywords")),
            key=f"keywords_{row['file_id']}",
            placeholder="e.g., virtual wall, cable hazard, brush jam",
        )

        st.text_area(
            "Excerpt",
            _clean(row.get("excerpt")),
            height=180,
            key=f"excerpt_{row['file_id']}",
            disabled=True,
        )

        if st.button("Save Row", key=f"save_{index}"):
            errors = []
            required_pairs = [
                ("Doc Type", doc_type),
                ("Product Line", product_line),
                ("Model", model),
                ("Software Version", software_version),
                ("Hardware Version", hardware_version),
                ("Subsystem", subsystem),
                ("Audience", audience),
                ("Priority", priority),
                ("Lifecycle", lifecycle),
                ("Confidentiality", confidentiality),
            ]
            for label, value in required_pairs:
                if not value:
                    errors.append(f"{label} is required.")

            if software_version == "Other" and not _clean(software_version_other):
                errors.append("Software Version (Other) must be provided when Software Version is Other.")
            if hardware_version == "Other" and not _clean(hardware_version_other):
                errors.append("Hardware Version (Other) must be provided when Hardware Version is Other.")
            if doc_type == "Other" and not _clean(keywords):
                errors.append("Keywords are required when Doc Type is Other.")

            if errors:
                for message in errors:
                    st.error(message)
            else:
                payload = {
                    "file_id": row["file_id"],
                    "doc_type": doc_type,
                    "product_line": product_line,
                    "model": model,
                    "software_version": software_version,
                    "software_version_other": _clean(software_version_other) if software_version == "Other" else "",
                    "hardware_version": hardware_version,
                    "hardware_version_other": _clean(hardware_version_other) if hardware_version == "Other" else "",
                    "subsystem": subsystem,
                    "audience": audience,
                    "priority": priority,
                    "lifecycle": lifecycle,
                    "confidentiality": confidentiality,
                    "keywords": keywords.strip(),
                }
                try:
                    update_from_csv_row(payload)
                except ValueError as exc:
                    st.error(str(exc))
                else:
                    st.success("Saved.")

st.download_button(
    "Export CSV",
    data=dataframe.to_csv(index=False).encode("utf-8"),
    file_name="inventory_labeled.csv",
    mime="text/csv",
)
