# Quick Start Guide

Get up and running with the OOI FAIR Pipeline in 5 minutes.

## Prerequisites

- Python 3.9 or higher
- OOI M2M API credentials ([Get them here](https://ooinet.oceanobservatories.org/))

## Installation

```bash
# 1. Navigate to project directory
cd ooi_fair_pipeline_project

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up credentials
cat > .env << EOF
OOI_API_USERNAME=your_username_here
OOI_API_TOKEN=your_token_here
EOF
```

## Basic Usage

### 1. Extract OOI Data

```bash
# Download CE02SHSM CTD data (example)
python3 src/extract/ooi_api.py
```

Output: `data/raw/test_download.nc`

### 2. Assess FAIR Compliance

```bash
# Evaluate downloaded dataset
python3 examples/assess_dataset.py data/raw/test_download.nc
```

Example output:
```
================================================================================
                          FAIR ASSESSMENT RESULTS
================================================================================

Overall FAIR Score: 86.7/100
Grade: B

Findable:       25.0/25 (100.0%) ████████████████████████████████████████ ✓
Accessible:     20.0/20 (100.0%) ████████████████████████████████████████ ✓
Interoperable:  19.7/30 (65.7%)  ██████████████████████████              ⚠
Reusable:       22.0/25 (88.0%)  ███████████████████████████████████     ⚠
```

### 3. Enrich Dataset

```bash
# Automatically improve FAIR compliance
python3 examples/enrich_dataset.py data/raw/test_download.nc
```

Output: `data/raw/test_download_enriched.nc`

### 4. Re-assess Enriched Data

```bash
# Verify improvements
python3 examples/assess_dataset.py data/raw/test_download_enriched.nc
```

Example output:
```
Overall FAIR Score: 93.0/100
Grade: A

Improvement: +6.3 points (B → A)
```

## Python API Usage

### Extract Data

```python
from src.extract.ooi_api import OOIDataExtractor

# Initialize extractor
extractor = OOIDataExtractor()

# Request data
result = extractor.request_data(
    array='CE02SHSM',
    site='RID27',
    node='03-CTDBPC000',
    method='telemetered',
    stream='ctdbp_cdef_dcl_instrument',
    start_date='2024-11-01T00:00:00.000Z',
    end_date='2024-11-30T23:59:59.999Z'
)

# Download when ready
downloaded = extractor.download_dataset(result['thredds_url'])
```

### Assess FAIR Compliance

```python
from src.assess.fair_assessor import FAIRAssessor

# Create assessor
assessor = FAIRAssessor('data/raw/test_download.nc')

# Run assessment
score = assessor.assess()

# Print results
print(f"FAIR Score: {score.total_score:.1f}/100 (Grade: {score.grade})")
print(f"  Findable:       {score.findable:.1f}/25")
print(f"  Accessible:     {score.accessible:.1f}/20")
print(f"  Interoperable:  {score.interoperable:.1f}/30")
print(f"  Reusable:       {score.reusable:.1f}/25")

# Get detailed report
assessor.print_report()

# Save JSON report
assessor.save_report('assessment_report.json')
```

### Enrich Dataset

```python
from src.transform.enrichment_pipeline import FAIREnrichmentPipeline

# Create pipeline
pipeline = FAIREnrichmentPipeline(
    input_path='data/raw/test_download.nc',
    output_path='data/raw/test_download_enriched.nc'
)

# Run enrichment
enriched = pipeline.run()

# Save enriched dataset
output_path = pipeline.save()

# Print summary
pipeline.print_summary()

# Get detailed changes
summary = pipeline.get_enrichment_summary()
print(f"Total changes: {summary['total_changes']}")
```

### Compare Before/After

```python
from src.transform.comparison import quick_compare

# Compare FAIR scores
quick_compare(
    'data/raw/test_download.nc',
    'data/raw/test_download_enriched.nc'
)
```

## Common Workflows

### Complete Pipeline (Command Line)

```bash
# 1. Extract → 2. Assess → 3. Enrich → 4. Re-assess
python3 src/extract/ooi_api.py && \
python3 examples/assess_dataset.py data/raw/test_download.nc && \
python3 examples/enrich_dataset.py data/raw/test_download.nc && \
python3 examples/assess_dataset.py data/raw/test_download_enriched.nc
```

### Batch Processing (Python)

```python
from pathlib import Path
from src.transform.enrichment_pipeline import quick_enrich
from src.assess.fair_assessor import FAIRAssessor

# Process all NetCDF files in a directory
input_dir = Path('data/raw')
output_dir = Path('data/enriched')
output_dir.mkdir(exist_ok=True)

for nc_file in input_dir.glob('*.nc'):
    if 'enriched' in nc_file.name:
        continue  # Skip already enriched files

    print(f"\nProcessing: {nc_file.name}")

    # Assess original
    original_score = FAIRAssessor(str(nc_file)).assess()
    print(f"  Original: {original_score.total_score:.1f}/100")

    # Enrich
    output_file = output_dir / f"{nc_file.stem}_enriched{nc_file.suffix}"
    quick_enrich(str(nc_file), str(output_file))

    # Assess enriched
    enriched_score = FAIRAssessor(str(output_file)).assess()
    print(f"  Enriched: {enriched_score.total_score:.1f}/100")
    print(f"  Improvement: +{enriched_score.total_score - original_score.total_score:.1f}")
```

## Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_fair_assessor.py

# Run with coverage report
pytest --cov=src --cov-report=html
open htmlcov/index.html  # View coverage report
```

## Troubleshooting

### Authentication Error

```
Error: AuthenticationError: Invalid OOI API credentials
```

**Solution**: Check your `.env` file has correct credentials:
```bash
cat .env
```

### Data Not Ready

```
Error: DataNotReadyError: Dataset not ready yet
```

**Solution**: OOI API requires time to prepare data. The script will retry automatically. Large date ranges may take 10-30 minutes.

### Missing Dependencies

```
ModuleNotFoundError: No module named 'xarray'
```

**Solution**: Ensure virtual environment is activated and dependencies installed:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### CF Compliance Checker Optional

Some tests require the optional `compliance-checker` package:
```bash
pip install compliance-checker
```

## Next Steps

- Read [README.md](README.md) for complete project overview
- Check [Sprint 2 Documentation](docs/SPRINT2_FAIR_ASSESSMENT.md) for assessment details
- Check [Sprint 3 Documentation](docs/SPRINT3_ENRICHMENT.md) for enrichment details
- Review [Testing Guide](docs/TESTING.md) for test suite documentation

## Support

- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Documentation**: `docs/` directory
- **Examples**: `examples/` directory

---

**Time to FAIR-compliant data: ~5 minutes** ⏱️
