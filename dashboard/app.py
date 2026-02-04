"""
MRV Readiness Dashboard

Streamlit app for assessing and enriching oceanographic NetCDF
datasets for marine carbon removal verification.

Start with:
    streamlit run dashboard/app.py
"""

import sys
from pathlib import Path
import tempfile
import json

import streamlit as st
import pandas as pd
import altair as alt
import xarray as xr

# Add src to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from assess.fair_assessor import FAIRAssessor
from transform.enrichment_pipeline import FAIREnrichmentPipeline
from transform.argo_enrichment_pipeline import ArgoEnrichmentPipeline

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="MRV Readiness",
    layout="wide",
)

HISTORY_FILE = PROJECT_ROOT / "data" / "dashboard_history.json"
GRADE_COLORS = {"A": "#22c55e", "B": "#84cc16", "C": "#eab308", "D": "#f97316", "F": "#ef4444"}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def detect_dataset_type(ds: xr.Dataset) -> str:
    """Detect if dataset is Argo or OOI format."""
    if "JULD" in ds.variables or "N_PROF" in ds.dims:
        return "argo"
    return "ooi"


def load_history() -> list:
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text())
    return []


def save_history(records: list):
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(records, indent=2))


def append_history(record: dict):
    records = load_history()
    records.append(record)
    save_history(records)


def score_to_dict(score) -> dict:
    """Convert FAIRScore object to serializable dict."""
    return {
        "total_score": round(score.total_score, 2),
        "grade": score.grade,
        "findable_score": round(score.findable_score, 2),
        "accessible_score": round(score.accessible_score, 2),
        "interoperable_score": round(score.interoperable_score, 2),
        "reusable_score": round(score.reusable_score, 2),
        "findable_details": [
            {"name": m.name, "points_earned": m.points_earned,
             "points_possible": m.points_possible, "percentage": m.percentage,
             "status": m.status, "details": m.details, "issues": list(m.issues)}
            for m in score.findable_details
        ],
        "accessible_details": [
            {"name": m.name, "points_earned": m.points_earned,
             "points_possible": m.points_possible, "percentage": m.percentage,
             "status": m.status, "details": m.details, "issues": list(m.issues)}
            for m in score.accessible_details
        ],
        "interoperable_details": [
            {"name": m.name, "points_earned": m.points_earned,
             "points_possible": m.points_possible, "percentage": m.percentage,
             "status": m.status, "details": m.details, "issues": list(m.issues)}
            for m in score.interoperable_details
        ],
        "reusable_details": [
            {"name": m.name, "points_earned": m.points_earned,
             "points_possible": m.points_possible, "percentage": m.percentage,
             "status": m.status, "details": m.details, "issues": list(m.issues)}
            for m in score.reusable_details
        ],
    }


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

st.sidebar.title("MRV Readiness")
st.sidebar.markdown("Make oceanographic data verification-ready for marine carbon removal.")
st.sidebar.divider()

st.sidebar.markdown("""
**What is the MRV Readiness Score?**

It measures how well a NetCDF file works as a
*standalone, self-documenting dataset* for
carbon removal verification.

Based on FAIR principles:
- **F**indable — Can verifiers discover it?
- **A**ccessible — Clear access terms?
- **I**nteroperable — Standard formats?
- **R**eusable — Quality documented?
""")

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_upload, tab_dashboard, tab_about = st.tabs(
    ["Assess & Enrich", "History", "About"]
)

# ---------------------------------------------------------------------------
# Tab 1 – Upload & Assess
# ---------------------------------------------------------------------------

with tab_upload:
    st.header("Assess & Enrich a Dataset")
    st.markdown(
        "Upload a NetCDF file to get its **MRV Readiness Score** and download "
        "an enriched version with improved metadata."
    )

    uploaded = st.file_uploader(
        "Choose a NetCDF file",
        type=["nc", "nc4", "netcdf"],
        help="Supports OOI and BGC-Argo NetCDF files",
    )

    if uploaded is not None:
        if st.button("Assess & Enrich", type="primary", use_container_width=True):
            with st.spinner("Processing..."):
                # Save uploaded file to temp location
                with tempfile.NamedTemporaryFile(suffix=".nc", delete=False) as tmp:
                    tmp.write(uploaded.getvalue())
                    tmp_path = Path(tmp.name)

                try:
                    # Detect type
                    ds = xr.open_dataset(tmp_path)
                    dataset_type = detect_dataset_type(ds)
                    ds.close()

                    # Assess original
                    assessor_orig = FAIRAssessor(str(tmp_path))
                    original_score = assessor_orig.assess()

                    # Enrich
                    enriched_path = tmp_path.parent / f"{tmp_path.stem}_enriched.nc"
                    if dataset_type == "argo":
                        pipeline = ArgoEnrichmentPipeline(str(tmp_path), str(enriched_path))
                    else:
                        pipeline = FAIREnrichmentPipeline(str(tmp_path), str(enriched_path))

                    pipeline.run()
                    pipeline.save()
                    summary = pipeline.get_enrichment_summary()

                    # Assess enriched
                    assessor_enr = FAIRAssessor(str(enriched_path))
                    enriched_score = assessor_enr.assess()

                    orig = score_to_dict(original_score)
                    enr = score_to_dict(enriched_score)
                    improvement = round(enriched_score.total_score - original_score.total_score, 2)

                    # Save to history
                    from datetime import datetime, timezone
                    append_history({
                        "filename": uploaded.name,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "dataset_type": dataset_type,
                        "original_score": orig,
                        "enriched_score": enr,
                        "improvement": improvement,
                    })

                    # ----- Results -----
                    st.divider()
                    st.subheader("Results")

                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Original Score", f"{orig['total_score']:.1f}/100")
                    col2.metric("Enriched Score", f"{enr['total_score']:.1f}/100",
                                f"+{improvement:.1f}")
                    col3.metric("Grade", f"{orig['grade']} → {enr['grade']}")
                    col4.metric("Dataset Type", dataset_type.upper())

                    # ----- Bar chart -----
                    st.divider()
                    st.subheader("MRV Readiness Breakdown")

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

                    # ----- Changes -----
                    changes = summary.get("enrichers", {})
                    if changes:
                        st.divider()
                        st.subheader("Enrichment Changes")
                        total_changes = sum(c.get("changes_made", 0) for c in changes.values())
                        st.markdown(f"**{total_changes} metadata enhancements applied**")
                        for name, info in changes.items():
                            st.markdown(
                                f"- **{name}**: {info['changes_made']} changes, "
                                f"{info['issues_found']} issues"
                            )

                    # ----- Metric details -----
                    st.divider()
                    st.subheader("Metric Details (Enriched)")

                    for principle in ["findable", "accessible", "interoperable", "reusable"]:
                        details = enr[f"{principle}_details"]
                        score_val = enr[f"{principle}_score"]
                        with st.expander(f"{principle.capitalize()} — {score_val:.1f} pts"):
                            for m in details:
                                icon = {"pass": "[PASS]",
                                        "partial": "[PARTIAL]",
                                        "fail": "[FAIL]"}.get(m["status"], "[?]")
                                st.markdown(
                                    f"{icon} **{m['name']}** — "
                                    f"{m['points_earned']:.1f}/{m['points_possible']:.0f} "
                                    f"({m['percentage']:.0f}%)"
                                )
                                if m["details"]:
                                    st.caption(m["details"])

                    # ----- Download -----
                    st.divider()
                    with open(enriched_path, "rb") as f:
                        enriched_bytes = f.read()

                    st.download_button(
                        "Download Enriched File",
                        data=enriched_bytes,
                        file_name=f"{uploaded.name.rsplit('.', 1)[0]}_enriched.nc",
                        mime="application/x-netcdf",
                        use_container_width=True,
                    )

                except Exception as e:
                    st.error(f"Error processing file: {e}")

# ---------------------------------------------------------------------------
# Tab 2 – Dashboard
# ---------------------------------------------------------------------------

with tab_dashboard:
    st.header("Assessment History")

    records = load_history()

    if not records:
        st.info("No assessments yet. Upload a file in the Assess tab to get started.")
    else:
        # Summary metrics
        orig_scores = [r.get("original_score", r.get("score", {})).get("total_score", 0) for r in records]
        enr_scores = [r.get("enriched_score", {}).get("total_score") for r in records if r.get("enriched_score")]

        col1, col2, col3 = st.columns(3)
        col1.metric("Files Processed", len(records))
        if orig_scores:
            col2.metric("Avg Original Score", f"{sum(orig_scores) / len(orig_scores):.1f}")
        if enr_scores:
            col3.metric("Avg Enriched Score", f"{sum(enr_scores) / len(enr_scores):.1f}")

        st.divider()

        # Table
        rows = []
        for r in records:
            score_data = r.get("enriched_score", r.get("score", {}))
            rows.append({
                "File": r.get("filename", "unknown"),
                "Type": r.get("dataset_type", "?").upper(),
                "Score": score_data.get("total_score", 0),
                "Grade": score_data.get("grade", "?"),
                "F": score_data.get("findable_score", 0),
                "A": score_data.get("accessible_score", 0),
                "I": score_data.get("interoperable_score", 0),
                "R": score_data.get("reusable_score", 0),
                "Improvement": r.get("improvement", "—"),
                "Time": r.get("timestamp", "")[:19],
            })

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Chart
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
                    tooltip=["File", "Type", "Score", "Grade", "Improvement"],
                )
                .properties(height=300)
            )
            st.altair_chart(score_chart, use_container_width=True)

        # Clear history
        st.divider()
        if st.button("Clear History", type="secondary"):
            save_history([])
            st.rerun()

# ---------------------------------------------------------------------------
# Tab 3 – About
# ---------------------------------------------------------------------------

with tab_about:
    st.header("About MRV Readiness")

    st.markdown("""
    ### What is this tool?

    This tool assesses and enriches oceanographic data to make it
    **verification-ready for marine carbon dioxide removal (mCDR)** projects.

    ### The Problem

    Raw oceanographic data (from Argo floats, OOI moorings, etc.) is designed
    for operational use by scientists. It often lacks the metadata needed for:

    - **Carbon credit verification** — Verifiers need self-contained, well-documented files
    - **Regulatory compliance** — EPA, London Protocol, and other frameworks require traceable data
    - **Long-term archival** — Data must be understandable decades from now

    ### The Solution

    This pipeline:

    1. **Assesses** your data against verification requirements
    2. **Enriches** it with missing metadata (identifiers, licenses, provenance, etc.)
    3. **Outputs** a standardized file ready for MRV workflows

    ### The MRV Readiness Score

    The score measures how well a dataset works as a **standalone, self-documenting file**
    for verification purposes. It's based on FAIR principles:

    | Principle | What it measures | Points |
    |-----------|------------------|--------|
    | **Findable** | Identifiers, descriptive metadata, discoverability | 25 |
    | **Accessible** | License, contact info, access protocols | 20 |
    | **Interoperable** | CF conventions, standard formats, coordinate systems | 30 |
    | **Reusable** | Provenance, quality documentation, community standards | 25 |

    **Important:** This score measures *file quality for verification*, not adherence
    to the source program's standards. Argo and OOI data are excellent for their
    intended purposes — this tool makes them work for verification too.

    ### Supported Datasets

    - **BGC-Argo** — Biogeochemical Argo floats (pH, O2, nitrate, chlorophyll)
    - **OOI** — Ocean Observatories Initiative (CTD, dissolved oxygen, etc.)

    ### Use Cases

    - **Ocean Alkalinity Enhancement (OAE)** — Use BGC-Argo pH data for baseline monitoring
    - **MRV for carbon credits** — Prepare data for third-party verification
    - **Regulatory submissions** — Create compliant data packages
    - **Research data management** — Improve discoverability and citation

    ### Links

    - [FAIR Principles](https://www.go-fair.org/fair-principles/)
    - [CF Conventions](https://cfconventions.org/)
    - [Biogeochemical Argo](https://biogeochemical-argo.org/)
    - [Carbon to Sea Initiative](https://www.carbontosea.org/)
    """)
