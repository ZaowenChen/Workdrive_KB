import pandas as pd
import streamlit as st

from src.db import all_for_csv, update_from_csv_row

st.set_page_config(page_title="WorkDrive Classification Review", layout="wide")
st.title("Document Classification Review")

rows = all_for_csv()
dataframe = pd.DataFrame(rows)

if dataframe.empty:
    st.info("No data yet. Run crawl/extract/classify first.")
    st.stop()

st.caption("Filter and correct labels. Click 'Save Row' to persist; 'Export CSV' for bulk ops.")

for index, row in dataframe.iterrows():
    with st.expander(row["path"], expanded=False):
        column1, column2, column3, column4, column5 = st.columns([2, 1, 1, 1, 1])
        with column1:
            st.write(row["name"])
        doc_type = column2.selectbox(
            "Document Type",
            ["", "SOP", "PCN", "Release Note", "Troubleshooting Guide", "Manual", "Specification", "Checklist"],
            index=0
            if not row["doc_type"]
            else ["", "SOP", "PCN", "Release Note", "Troubleshooting Guide", "Manual", "Specification", "Checklist"].index(row["doc_type"]),
        )
        model = column3.selectbox(
            "Model",
            ["", "S50", "V40", "Scrubber75", "S1", "Workstation"],
            index=0
            if not row["model_type"]
            else ["", "S50", "V40", "Scrubber75", "S1", "Workstation"].index(row["model_type"]),
        )
        subsystem = column4.selectbox(
            "Subsystem",
            ["", "Laser", "Software", "Battery", "Drive", "Pump", "UI", "Network", "Other"],
            index=0
            if not row["subsystem"]
            else ["", "Laser", "Software", "Battery", "Drive", "Pump", "UI", "Network", "Other"].index(row["subsystem"]),
        )
        language = column5.selectbox(
            "Language",
            ["", "English", "Chinese", "Spanish", "Other"],
            index=0
            if not row["language"]
            else ["", "English", "Chinese", "Spanish", "Other"].index(row["language"]),
        )
        st.text_area(
            "Excerpt",
            "",
            placeholder="Open CSV export to view full excerpt in a spreadsheet if needed.",
            height=80,
        )
        if st.button("Save Row", key=f"save_{index}"):
            update_from_csv_row(
                {
                    "file_id": row["file_id"],
                    "doc_type": doc_type,
                    "model_type": model,
                    "subsystem": subsystem,
                    "language": language,
                }
            )
            st.success("Saved.")

st.download_button(
    "Export CSV",
    data=dataframe.to_csv(index=False).encode("utf-8"),
    file_name="inventory_labeled.csv",
    mime="text/csv",
)
