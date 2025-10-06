import math

import pandas as pd
import streamlit as st

from src.db import all_for_csv, update_from_csv_row

st.set_page_config(page_title="WorkDrive Classification Review", layout="wide")
st.title("Document Classification Review")

rows = all_for_csv()
dataframe = pd.DataFrame(rows).fillna("")

if dataframe.empty:
    st.info("No data yet. Run crawl/extract/classify first.")
    st.stop()

st.caption("Filter and correct labels. Click 'Save Row' to persist; 'Export CSV' for bulk ops.")

doc_type_options = ["", "SOP", "PCN", "Release Note", "Troubleshooting Guide", "Manual", "Specification", "Checklist"]
model_options = ["", "S50", "V40", "Scrubber75", "S1", "Workstation", "S50 & V40", "(Beetle) SW", "Genric"]
subsystem_options = ["", "Laser", "Software", "Battery", "Drive", "Pump", "UI", "Network", "Other"]
language_options = ["", "English", "Chinese", "Spanish", "Other"]
hardware_options = ["", "4.2", "4.1", "3.7", "3.6", "1.6", "1.5", "1.4.5", "1.4", "1.3", "1.2", "1.1", "1.0", "2.2.3"]
software_options = ["", "AIO1", "AIO2", "AIO3", "AIO4", "AIO5", "M Series"]
priority_options = ["", "high", "normal", "low"]
audience_options = ["", "intro", "operator", "technician", "engineer", "admin"]


def _normalize(value):
    if isinstance(value, str):
        return value
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return str(value)


def _safe_index(options: list[str], value) -> int:
    normalized = _normalize(value)
    if normalized in options:
        return options.index(normalized)
    return 0


for index, row in dataframe.iterrows():
    with st.expander(row["path"], expanded=False):
        column1, column2, column3, column4, column5 = st.columns([2, 1, 1, 1, 1])
        with column1:
            st.write(row["name"])
            st.caption(row["path"])
            links = []
            permalink = _normalize(row.get("permalink"))
            download_url = _normalize(row.get("download_url"))
            if permalink:
                links.append(f"[Open]({permalink})")
            if download_url:
                links.append(f"[Download]({download_url})")
            if links:
                st.markdown(" • ".join(links))
        doc_type = column2.selectbox(
            "Document Type",
            doc_type_options,
            index=_safe_index(doc_type_options, row.get("doc_type")),
            key=f"doc_type_{row['file_id']}",
        )
        model = column3.selectbox(
            "Model",
            model_options,
            index=_safe_index(model_options, row.get("model_type")),
            key=f"model_{row['file_id']}",
        )
        subsystem = column4.selectbox(
            "Subsystem",
            subsystem_options,
            index=_safe_index(subsystem_options, row.get("subsystem")),
            key=f"subsystem_{row['file_id']}",
        )
        language = column5.selectbox(
            "Language",
            language_options,
            index=_safe_index(language_options, row.get("language")),
            key=f"language_{row['file_id']}",
        )

        col_hw, col_sw, col_priority, col_audience = st.columns(4)
        hardware_version = col_hw.selectbox(
            "Hardware Version",
            hardware_options,
            index=_safe_index(hardware_options, row.get("hardware_version")),
            key=f"hardware_{row['file_id']}",
        )
        software_version = col_sw.selectbox(
            "Software Version",
            software_options,
            index=_safe_index(software_options, row.get("software_version")),
            key=f"software_{row['file_id']}",
        )
        priority = col_priority.selectbox(
            "Priority",
            priority_options,
            index=_safe_index(priority_options, row.get("priority")),
            key=f"priority_{row['file_id']}",
        )
        audience_level = col_audience.selectbox(
            "Audience Level",
            audience_options,
            index=_safe_index(audience_options, row.get("audience_level")),
            key=f"audience_{row['file_id']}",
        )

        st.text_area(
            "Excerpt",
            _normalize(row.get("excerpt")),
            height=120,
            key=f"excerpt_{row['file_id']}",
        )
        if st.button("Save Row", key=f"save_{index}"):
            update_from_csv_row(
                {
                    "file_id": row["file_id"],
                    "doc_type": doc_type,
                    "model_type": model,
                    "subsystem": subsystem,
                    "language": language,
                    "hardware_version": hardware_version,
                    "software_version": software_version,
                    "priority": priority,
                    "audience_level": audience_level,
                }
            )
            st.success("Saved.")

st.download_button(
    "Export CSV",
    data=dataframe.to_csv(index=False).encode("utf-8"),
    file_name="inventory_labeled.csv",
    mime="text/csv",
)
