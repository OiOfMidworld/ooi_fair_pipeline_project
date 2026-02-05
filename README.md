# MRV Readiness Pipeline

Data infrastructure for marine carbon dioxide removal (mCDR) verification.

Transform BGC-Argo and OOI oceanographic data into MRV-grade datasets with FAIR compliance and AI-powered quality assessment.

## Why This Matters

> "As mCDR progresses toward deployment and regulation, Findable, Accessible, Interoperable and Reuseable (FAIR) data should be **mandatory** for project approval and inclusion in national or international carbon inventories."
>
> — European Marine Board, *MRV for Marine CDR* (2025)

The mCDR industry (ocean alkalinity enhancement, kelp farming, direct ocean capture) is scaling rapidly, but verification infrastructure doesn't exist yet:

> "At present, no mCDR method has a mature, independently verifiable, end-to-end MRV system suitable for large-scale deployment."
>
> — EMB 2025, Section 8.3

This pipeline addresses that gap by transforming raw oceanographic observations into verification-ready datasets.

## What It Does

**Before:** Raw BGC-Argo data scores 49/100 (Grade F) on MRV readiness

**After:** Enriched data scores 92/100 (Grade A)

The pipeline:
1. **Assesses** datasets against FAIR/MRV requirements
2. **Detects anomalies** using ML (IsolationForest on pH data)
3. **Enriches** metadata for verification workflows
4. **Outputs** CF-compliant, auditable NetCDF files

## Quick Start

```bash
# Install
cd ooi_fair_pipeline_project
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Run dashboard
python3 -m streamlit run dashboard/app.py
```

Open http://localhost:8501 to upload and process files.

## Features

### FAIR Assessment
- 100-point scoring across Findable, Accessible, Interoperable, Reusable
- Detailed metric-by-metric breakdown
- Actionable improvement recommendations

### AI Anomaly Detection
- IsolationForest trained on historical BGC-Argo pH profiles
- Flags suspicious measurements considering depth and temperature context
- Adds CF-compliant `PH_ANOMALY_FLAG` variable to output

### Metadata Enrichment
- Adds CF standard names, units, coordinate metadata
- Documents provenance and quality control methodology
- Generates unique identifiers and licensing info

## Supported Data

| Source | Variables | Use Case |
|--------|-----------|----------|
| **BGC-Argo** | pH, O2, nitrate, chlorophyll | OAE baseline monitoring |
| **OOI** | CTD, dissolved oxygen | Coastal mCDR projects |

## API

```python
from src.assess.fair_assessor import FAIRAssessor
from src.transform.argo_enrichment_pipeline import ArgoEnrichmentPipeline

# Assess
score = FAIRAssessor('data.nc').assess()
print(f"{score.total_score}/100 (Grade {score.grade})")

# Enrich (includes anomaly detection)
pipeline = ArgoEnrichmentPipeline('input.nc', 'output.nc')
pipeline.run()
pipeline.save()
```

REST API available at `uvicorn api.main:app --port 8000`

## Project Structure

```
src/
├── assess/          # FAIR scoring engine
├── extract/         # BGC-Argo and OOI data download
├── transform/       # Enrichment pipeline + anomaly detection
├── qc/              # ML models (IsolationForest)
└── utils/           # Logging, exceptions

dashboard/           # Streamlit web interface
api/                 # FastAPI REST endpoints
scripts/             # Training scripts
```

## Regulatory Alignment

This tool addresses recommendations from the [EMB MRV Report (2025)](https://www.marineboard.eu/publications/MRV_for_mCDR):

| EMB Recommendation | How We Address It |
|-------------------|-------------------|
| #11: Transparent data-sharing | Open-access, auditable outputs |
| #14: Establish robust baselines | ML baseline modeling (in progress) |
| #15: Quantify uncertainties | Anomaly scoring with confidence |
| #22: FAIR data stewardship | Automated FAIR compliance |

## Roadmap

- [x] FAIR assessment engine
- [x] BGC-Argo and OOI support
- [x] pH anomaly detection (IsolationForest)
- [ ] Baseline modeling (seasonal/regional patterns)
- [ ] Uncertainty quantification
- [ ] Export to GLODAP/SOCAT formats

## Links

**Standards:**
- [FAIR Principles](https://www.go-fair.org/fair-principles/)
- [CF Conventions](https://cfconventions.org/)

**Data Sources:**
- [BGC-Argo](https://biogeochemical-argo.org/)
- [OOI Data Portal](https://ooinet.oceanobservatories.org/)

**mCDR/MRV:**
- [EMB MRV Report (2025)](https://www.marineboard.eu/publications/MRV_for_mCDR)
- [Carbon to Sea Initiative](https://www.carbontosea.org/)
- [Ocean Visions](https://oceanvisions.org/)

## Requirements

Python 3.9+. See [requirements.txt](requirements.txt) for dependencies.
