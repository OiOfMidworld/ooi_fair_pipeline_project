# OOI FAIR Pipeline Project

**Automated ETL pipeline for Ocean Observatories Initiative (OOI) data with FAIR compliance enhancement**

Transform raw oceanographic data into FAIR-compliant, analysis-ready datasets.

## Project Status

| Sprint | Status | Score Impact | Documentation |
|--------|--------|--------------|---------------|
| Sprint 0: Foundation | Complete | Baseline: 35/100 (F) | Setup & Discovery |
| Sprint 1: Data Extraction | Complete | - | [Extraction Pipeline](docs/) |
| Sprint 2: FAIR Assessment | Complete | Measured: 86.7/100 (B) | [SPRINT2_FAIR_ASSESSMENT.md](docs/SPRINT2_FAIR_ASSESSMENT.md) |
| Sprint 3: Data Enrichment | Complete | 93.0/100 (A)** | [SPRINT3_DATA_ENRICHMENT.md](docs/SPRINT3_DATA_ENRICHMENT.md) |
| Sprint 4: Integration | Planned | | |

## What This Project Does

The OOI FAIR Pipeline is an end-to-end ETL (Extract, Transform, Load) system that:

1. **Extracts** oceanographic data from OOI's M2M API
2. **Assesses** FAIR compliance scores
3. **Enriches** metadata to improve interoperability
4. **Validates** CF conventions compliance
5. **Reports** improvements and remaining gaps

**Result:** Transforms raw OOI data from **Grade F to Grade A** on FAIR principles.

## Key Features

### Data Extraction (Sprint 1)
- Automated M2M API authentication
- THREDDS catalog parsing
- Batch download with retry logic
- Comprehensive error handling and logging

### FAIR Assessment (Sprint 2)
- Evaluates datasets against FAIR principles (100-point scale)
- CF conventions compliance checking
- Detailed metric-by-metric scoring
- Actionable improvement recommendations
- JSON report generation

### Data Enrichment (Sprint 3)
- **+6.3 point FAIR improvement** (B → A grade)
- Adds missing coordinate variables (lat/lon/depth)
- Enriches variable metadata (units, standard_name, long_name)
- Enhances global attributes (ACDD compliance)
- Automated CF compliance fixes
- Before/after comparison reporting

## Quick Start

### Installation

```bash
# Clone repository
git clone <repository-url>
cd ooi_fair_pipeline_project

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up OOI API credentials
cp .env.example .env
# Edit .env with your OOI credentials
```

### Extract OOI Data

```bash
python3 src/extract/ooi_api.py
```

### Assess FAIR Compliance

```bash
python3 examples/assess_dataset.py data/raw/your_dataset.nc
```

### Enrich Dataset

```bash
python3 examples/enrich_dataset.py data/raw/your_dataset.nc
```

## Example Results

**Before Enrichment:**
```
FAIR Score: 86.7/100 (Grade: B)
  Findable:       25.0/25 
  Accessible:     20.0/20 
  Interoperable:  19.7/30 
  Reusable:       22.0/25 
```

**After Enrichment:**
```
FAIR Score: 93.0/100 (Grade: A)
  Findable:       25.0/25 
  Accessible:     20.0/20 
  Interoperable:  23.0/30 
  Reusable:       25.0/25 

Improvement: +6.3 points (B → A)
Changes applied: 27
```

## Project Structure

```
ooi_fair_pipeline_project/
├── src/
│   ├── extract/              # Data extraction (Sprint 1)
│   │   ├── ooi_api.py        # M2M API client
│   │   ├── config.py         # Instrument configurations
│   │   └── discover_instruments.py
│   ├── assess/               # FAIR assessment (Sprint 2)
│   │   ├── fair_assessor.py  # Main assessment engine
│   │   ├── fair_metrics.py   # Scoring rubric
│   │   └── cf_checker.py     # CF compliance
│   ├── transform/            # Data enrichment (Sprint 3)
│   │   ├── enrichment_pipeline.py
│   │   ├── coordinate_enricher.py
│   │   ├── variable_enricher.py
│   │   ├── metadata_enricher.py
│   │   └── comparison.py
│   └── utils/                # Shared utilities
│       ├── logging_config.py
│       └── exceptions.py
├── examples/                 # Demo scripts
│   ├── assess_dataset.py
│   └── enrich_dataset.py
├── tests/                    # Test suite (68 tests)
├── docs/                     # Documentation
│   ├── SPRINT2_FAIR_ASSESSMENT.md
│   ├── SPRINT3_DATA_ENRICHMENT.md
│   ├── LOGGING_AND_ERRORS.md
│   └── TESTING.md
├── data/
│   ├── raw/                  # Downloaded OOI data
│   └── enriched/             # Processed datasets
└── requirements.txt
```

## Target Array & Instruments

**Focus:** Coastal Endurance Array - Oregon Shelf Surface Mooring (CE02SHSM)

**Instruments:**
- CTD (Conductivity-Temperature-Depth) - Primary sensor
- Dissolved Oxygen sensor
- Additional sensors TBD in future sprints

## FAIR Principles Coverage

### F - Findable
- Unique persistent identifiers
- Rich descriptive metadata
- Searchable attributes (geospatial, temporal)
- Standard metadata conventions (CF, ACDD)

### A - Accessible
- Standard access protocols (HTTP/OPeNDAP)
- Contact information
- Usage license specified
- Metadata retrievability

### I - Interoperable
- CF Conventions compliance
- Standard vocabularies (CF standard names)
- NetCDF format
- Coordinate system definitions

### R - Reusable
- Clear usage license
- Data provenance
- Quality control documentation
- Community standards (OOI, CF)

## Documentation

- **[Sprint 2: FAIR Assessment](docs/SPRINT2_FAIR_ASSESSMENT.md)** - Assessment engine details
- **[Sprint 3: Data Enrichment](docs/SPRINT3_DATA_ENRICHMENT.md)** - Enrichment pipeline guide
- **[Testing Guide](docs/TESTING.md)** - Test suite documentation
- **[Logging & Errors](docs/LOGGING_AND_ERRORS.md)** - Error handling reference

## Usage Examples

### Python API

```python
# Extract data
from src.extract.ooi_api import OOIDataExtractor

extractor = OOIDataExtractor()
result = extractor.request_data(
    array='CE02SHSM',
    site='RID27',
    node='03-CTDBPC000',
    method='telemetered',
    stream='ctdbp_cdef_dcl_instrument',
    start_date='2024-11-01T00:00:00.000Z',
    end_date='2024-11-30T23:59:59.999Z'
)

# Assess FAIR compliance
from src.assess.fair_assessor import FAIRAssessor

assessor = FAIRAssessor('data/raw/dataset.nc')
score = assessor.assess()
print(f"FAIR Score: {score.total_score:.1f}/100")

# Enrich dataset
from src.transform.enrichment_pipeline import quick_enrich

output = quick_enrich('data/raw/dataset.nc')
print(f"Enriched dataset: {output}")
```

### Command Line

```bash
# Run full pipeline
python3 src/extract/ooi_api.py
python3 examples/assess_dataset.py data/raw/test_download.nc
python3 examples/enrich_dataset.py data/raw/test_download.nc
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test module
pytest tests/test_fair_assessor.py -v
```

**Test Status:** 68 passing, 15 skipped (92% pass rate)

## Requirements

- Python 3.9+
- xarray
- netCDF4
- numpy
- requests
- compliance-checker
- python-dotenv
- pytest (for testing)

See [requirements.txt](requirements.txt) for complete list.

## OOI API Credentials

You'll need OOI M2M API credentials:

1. Create account at [OOI Data Portal](https://ooinet.oceanobservatories.org/)
2. Get API username and token from user profile
3. Add to `.env` file:

```bash
OOI_API_USERNAME=your_username
OOI_API_TOKEN=your_token
```

## Contributing

This is a research project. Contributions welcome via:
- Bug reports
- Feature requests
- Documentation improvements
- Code contributions (follow existing patterns)

## Future Work (Sprint 4+)

### Sprint 4: Integration & Deployment
- [ ] RESTful API for enrichment service
- [ ] Batch processing for multiple datasets
- [ ] FAIR score monitoring dashboard
- [ ] Cloud deployment (AWS/GCP)
- [ ] Integration with OOI data portal

### Long-term Roadmap
- [ ] Support for more OOI instruments
- [ ] Machine learning for metadata inference
- [ ] Real-time enrichment at data ingest
- [ ] Linked data / semantic web support
- [ ] Integration with data repositories (Zenodo, DataONE)

## References

- [FAIR Principles](https://www.go-fair.org/fair-principles/)
- [CF Conventions](http://cfconventions.org/)
- [ACDD Standard](https://wiki.esipfed.org/Attribute_Convention_for_Data_Discovery)
- [Ocean Observatories Initiative](https://oceanobservatories.org/)
- [OOI M2M API Documentation](https://oceanobservatories.org/data-access/)

## License

[Add license information]

## Contact

[Add contact information]

---

**Project Goal:** Make ocean observing data more Findable, Accessible, Interoperable, and Reusable for the scientific community.

**Status:** Sprint 3 Complete | 93/100 FAIR Score Achieved
