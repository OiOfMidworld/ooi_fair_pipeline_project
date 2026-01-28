"""
FAIR Pipeline Dashboard

Streamlit frontend for uploading, assessing, and enriching
oceanographic NetCDF datasets.

Start with:
    streamlit run dashboard/app.py
"""

import streamlit as st
import requests
import pandas as pd
import altair as alt
import json
from pathlib import Path

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="FAIR Pipeline",
    page_icon=":ocean:",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

GRADE_COLORS = {"A": "#22c55e", "B": "#84cc16", "C": "#eab308", "D": "#f97316", "F": "#ef4444"}


def grade_color(grade: str) -> str:
    return GRADE_COLORS.get(grade, "#6b7280")


def api_available() -> bool:
    try:
        r = requests.get(f"{API_URL}/health", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

st.sidebar.title(":ocean: FAIR Pipeline")
st.sidebar.markdown("Assess & enrich oceanographic data for FAIR compliance.")
st.sidebar.divider()

if api_available():
    st.sidebar.success("API connected")
else:
    st.sidebar.error(
        "API not running. Start it with:\n\n"
        "```\nuvicorn api.main:app --reload --port 8000\n```"
    )

tab_upload, tab_dashboard, tab_about = st.tabs(
    [":arrow_up: Upload & Assess", ":bar_chart: Dashboard", ":books: About"]
)

# ---------------------------------------------------------------------------
# Tab 1 – Upload & Assess
# ---------------------------------------------------------------------------

with tab_upload:
    st.header("Upload & Assess a Dataset")
    st.markdown("Upload a NetCDF file to get its FAIR score and an enriched version.")

    uploaded = st.file_uploader(
        "Choose a NetCDF file",
        type=["nc", "nc4", "netcdf"],
        help="Supports OOI and BGC-Argo NetCDF files",
    )

    if uploaded is not None:
        if st.button("Assess & Enrich", type="primary", use_container_width=True):
            if not api_available():
                st.error("API is not running. Please start the API server first.")
            else:
                with st.spinner("Processing..."):
                    files = {"file": (uploaded.name, uploaded.getvalue(), "application/x-netcdf")}
                    resp = requests.post(f"{API_URL}/assess-and-enrich", files=files, timeout=120)

                if resp.status_code != 200:
                    st.error(f"Error: {resp.json().get('detail', resp.text)}")
                else:
                    data = resp.json()
                    orig = data["original_score"]
                    enr = data["enriched_score"]

                    # ----- Header metrics -----
                    st.divider()
                    st.subheader("Results")

                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Original Score", f"{orig['total_score']:.1f}/100", None)
                    col2.metric("Enriched Score", f"{enr['total_score']:.1f}/100",
                                f"+{data['improvement']:.1f}")
                    col3.metric("Grade", f"{orig['grade']} -> {enr['grade']}")
                    col4.metric("Dataset Type", data["dataset_type"].upper())

                    # ----- Before / After bar chart -----
                    st.divider()
                    st.subheader("FAIR Principle Breakdown")

                    principles = ["Findable", "Accessible", "Interoperable", "Reusable"]
                    max_pts = [25, 20, 30, 25]
                    orig_vals = [orig["findable_score"], orig["accessible_score"],
                                 orig["interoperable_score"], orig["reusable_score"]]
                    enr_vals = [enr["findable_score"], enr["accessible_score"],
                                enr["interoperable_score"], enr["reusable_score"]]

                    chart_df = pd.DataFrame({
                        "Principle": principles * 2,
                        "Score": orig_vals + enr_vals,
                        "Max": max_pts * 2,
                        "Version": ["Original"] * 4 + ["Enriched"] * 4,
                    })
                    chart_df["Percentage"] = (chart_df["Score"] / chart_df["Max"] * 100).round(1)

                    bar = (
                        alt.Chart(chart_df)
                        .mark_bar()
                        .encode(
                            x=alt.X("Principle:N", sort=principles,
                                     axis=alt.Axis(labelAngle=0)),
                            y=alt.Y("Score:Q", title="Points"),
                            color=alt.Color("Version:N",
                                            scale=alt.Scale(
                                                domain=["Original", "Enriched"],
                                                range=["#94a3b8", "#22c55e"],
                                            )),
                            xOffset="Version:N",
                            tooltip=["Principle", "Version", "Score", "Max", "Percentage"],
                        )
                        .properties(height=350)
                    )
                    st.altair_chart(bar, use_container_width=True)

                    # ----- Enrichment changes -----
                    if data.get("enrichment_changes"):
                        st.divider()
                        st.subheader("Enrichment Changes")
                        for ch in data["enrichment_changes"]:
                            st.markdown(
                                f"**{ch['enricher']}** — "
                                f"{ch['changes_made']} changes, "
                                f"{ch['issues_found']} issues"
                            )

                    # ----- Metric details (expandable) -----
                    st.divider()
                    st.subheader("Metric Details (Enriched)")

                    for principle in ["findable", "accessible", "interoperable", "reusable"]:
                        details = enr[f"{principle}_details"]
                        with st.expander(f"{principle.capitalize()} — "
                                         f"{enr[f'{principle}_score']:.1f} pts"):
                            for m in details:
                                icon = {"pass": ":white_check_mark:",
                                        "partial": ":warning:",
                                        "fail": ":x:"}.get(m["status"], ":question:")
                                st.markdown(
                                    f"{icon} **{m['name']}** — "
                                    f"{m['points_earned']:.1f}/{m['points_possible']:.0f} "
                                    f"({m['percentage']:.0f}%)"
                                )
                                if m["details"]:
                                    st.caption(m["details"])

                    # ----- Download enriched file -----
                    st.divider()
                    enriched_name = data["enriched_filename"]
                    dl_resp = requests.get(f"{API_URL}/download/{enriched_name}", timeout=30)
                    if dl_resp.status_code == 200:
                        st.download_button(
                            ":arrow_down: Download Enriched File",
                            data=dl_resp.content,
                            file_name=enriched_name,
                            mime="application/x-netcdf",
                            use_container_width=True,
                        )

# ---------------------------------------------------------------------------
# Tab 2 – Dashboard
# ---------------------------------------------------------------------------

with tab_dashboard:
    st.header("Assessment Dashboard")

    if not api_available():
        st.info("Start the API to view assessment history.")
    else:
        resp = requests.get(f"{API_URL}/history", timeout=10)
        if resp.status_code != 200:
            st.error("Failed to load history.")
        else:
            hist = resp.json()

            if hist["total_processed"] == 0:
                st.info("No assessments yet. Upload a file in the Upload tab to get started.")
            else:
                # Summary metrics
                col1, col2, col3 = st.columns(3)
                col1.metric("Files Processed", hist["total_processed"])
                if hist["average_original_score"] is not None:
                    col2.metric("Avg Original Score",
                                f"{hist['average_original_score']:.1f}")
                if hist["average_enriched_score"] is not None:
                    col3.metric("Avg Enriched Score",
                                f"{hist['average_enriched_score']:.1f}")

                st.divider()

                # Table of assessments
                rows = []
                for a in hist["assessments"]:
                    rows.append({
                        "File": a["filename"],
                        "Type": a["dataset_type"].upper(),
                        "Score": a["score"]["total_score"],
                        "Grade": a["score"]["grade"],
                        "F": a["score"]["findable_score"],
                        "A": a["score"]["accessible_score"],
                        "I": a["score"]["interoperable_score"],
                        "R": a["score"]["reusable_score"],
                        "Timestamp": a["timestamp"][:19],
                    })

                df = pd.DataFrame(rows)
                st.dataframe(df, use_container_width=True, hide_index=True)

                # Score distribution chart
                if len(df) > 1:
                    st.divider()
                    st.subheader("Score Distribution")

                    score_chart = (
                        alt.Chart(df)
                        .mark_bar()
                        .encode(
                            x=alt.X("File:N", axis=alt.Axis(labelAngle=-45)),
                            y=alt.Y("Score:Q", scale=alt.Scale(domain=[0, 100])),
                            color=alt.Color("Grade:N",
                                            scale=alt.Scale(
                                                domain=list(GRADE_COLORS.keys()),
                                                range=list(GRADE_COLORS.values()),
                                            )),
                            tooltip=["File", "Type", "Score", "Grade"],
                        )
                        .properties(height=300)
                    )
                    st.altair_chart(score_chart, use_container_width=True)

# ---------------------------------------------------------------------------
# Tab 3 – About
# ---------------------------------------------------------------------------

with tab_about:
    st.header("About the FAIR Pipeline")

    st.markdown("""
    ### What is FAIR?

    The **FAIR Principles** ensure scientific data is:

    | Principle | Description | Points |
    |-----------|-------------|--------|
    | **F**indable | Rich metadata, unique identifiers, searchable | 25 |
    | **A**ccessible | Open protocols, contact info, license | 20 |
    | **I**nteroperable | CF conventions, standard names, NetCDF | 30 |
    | **R**eusable | License, provenance, QC documentation | 25 |

    ### Supported Datasets

    - **OOI** — Ocean Observatories Initiative (CE02SHSM array)
    - **BGC-Argo** — Biogeochemical Argo floats (pH, O2, nitrate, chlorophyll)

    ### mCDR / MRV Application

    This pipeline is designed to make oceanographic data **verification-ready**
    for marine Carbon Dioxide Removal (mCDR) projects, including:

    - **Ocean Alkalinity Enhancement (OAE)** monitoring
    - **Measurement, Reporting, Verification (MRV)** compliance
    - Carbon credit verification using BGC-Argo float data

    ### How It Works

    1. **Upload** a NetCDF file (OOI or BGC-Argo)
    2. **Assess** — the pipeline scores the file against FAIR principles
    3. **Enrich** — missing metadata is automatically added
    4. **Download** the enriched, verification-ready dataset

    ### Links

    - [FAIR Principles](https://www.go-fair.org/fair-principles/)
    - [CF Conventions](https://cfconventions.org/)
    - [Biogeochemical Argo](https://biogeochemical-argo.org/)
    - [Carbon to Sea Initiative](https://www.carbontosea.org/)
    """)
