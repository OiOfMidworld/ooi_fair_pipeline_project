# MRV Readiness Pipeline

Make oceanographic data verification-ready for marine carbon dioxide removal (mCDR) projects.

## What This Tool Does

The MRV Readiness Pipeline assesses and enriches NetCDF oceanographic datasets for use in carbon removal verification workflows. It transforms raw data from BGC-Argo floats and OOI moorings into self-documenting, standards-compliant files ready for third-party verification.

**Before:** Raw BGC-Argo data scores 49/100 (Grade F) on MRV readiness
**After:** Enriched data scores 92/100 (Grade A)

## Quick Start

### Installation

```bash
cd ooi_fair_pipeline_project

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Run the Streamlit Dashboard

```bash
python3 -m streamlit run dashboard/app.py
```

Open http://localhost:8501 in your browser to:
- Upload NetCDF files
- View MRV Readiness scores
- Download enriched files
- Track assessment history

### Run the API Server

```bash
uvicorn api.main:app --reload --port 8000
```

API endpoints at http://localhost:8000:
- `POST /assess` - Get MRV Readiness score for a file
- `POST /enrich` - Download enriched version of a file
- `POST /assess-and-enrich` - Assess, enrich, and compare scores
- `GET /history` - View assessment history

## Supported Datasets

- **BGC-Argo** - Biogeochemical Argo floats (pH, O2, nitrate, chlorophyll)
- **OOI** - Ocean Observatories Initiative (CTD, dissolved oxygen, etc.)

The pipeline auto-detects dataset type based on file contents.

## MRV Readiness Score

The score measures how well a dataset works as a standalone, self-documenting file for verification purposes. Based on FAIR principles:

| Principle | Points | What It Measures |
|-----------|--------|------------------|
| Findable | 25 | Identifiers, descriptive metadata, discoverability |
| Accessible | 20 | License, contact info, access protocols |
| Interoperable | 30 | CF conventions, standard formats, coordinates |
| Reusable | 25 | Provenance, quality documentation, standards |

**Grades:** A (90+), B (80-89), C (70-79), D (60-69), F (<60)

## Project Structure

```
ooi_fair_pipeline_project/
├── dashboard/
│   └── app.py              # Streamlit web interface
├── api/
│   ├── main.py             # FastAPI endpoints
│   └── models.py           # Pydantic response models
├── src/
│   ├── assess/             # FAIR assessment engine
│   ├── extract/            # Data download (OOI, BGC-Argo)
│   ├── transform/          # Enrichment pipeline
│   └── utils/              # Logging, exceptions
├── data/
│   ├── raw/                # Original datasets
│   └── enriched/           # Processed datasets
└── tests/                  # Test suite
```

## Python API

```python
# Assess a dataset
from src.assess.fair_assessor import FAIRAssessor

assessor = FAIRAssessor('data/raw/dataset.nc')
score = assessor.assess()
print(f"MRV Readiness: {score.total_score:.1f}/100 (Grade {score.grade})")

# Enrich a dataset
from src.transform.enrichment_pipeline import FAIREnrichmentPipeline

pipeline = FAIREnrichmentPipeline('input.nc', 'output_enriched.nc')
pipeline.run()
pipeline.save()
```

## Use Cases

- **Ocean Alkalinity Enhancement (OAE)** - Prepare BGC-Argo pH data for baseline monitoring
- **Carbon credit verification** - Create verification-ready data packages
- **Regulatory submissions** - EPA, London Protocol compliance
- **Research data management** - Improve discoverability and citation

## Requirements

- Python 3.9+
- See requirements.txt for dependencies

## Links

- [FAIR Principles](https://www.go-fair.org/fair-principles/)
- [CF Conventions](https://cfconventions.org/)
- [Biogeochemical Argo](https://biogeochemical-argo.org/)
- [Carbon to Sea Initiative](https://www.carbontosea.org/)
