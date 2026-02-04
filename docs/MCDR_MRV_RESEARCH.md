# Marine CDR & MRV: Research Summary

**Date:** January 28, 2026
**Focus:** Adapting OOI-FAIR Pipeline for marine Carbon Dioxide Removal (mCDR) applications

## Executive Summary

Marine Carbon Dioxide Removal (mCDR) is emerging as a critical climate solution, but **MRV (Measurement, Reporting, Verification) remains the biggest challenge**. Current MRV costs can exceed **50% of total project costs**, and data quality/standardization issues are major barriers to scaling.

**Opportunity:** Your FAIR pipeline can address a critical gap by:
1. Standardizing BGC-Argo and OAE monitoring data
2. Improving data quality for carbon accounting
3. Enabling credible, verifiable carbon removal claims
4. Reducing MRV costs through automation

## Marine CDR Landscape

### Key Technologies

1. **Ocean Alkalinity Enhancement (OAE)** - Most mature
   - Add alkaline minerals to seawater
   - Increases CO2 absorption capacity
   - Multiple startups scaling (Vycarb, Vesta, etc.)

2. **Enhanced Rock Weathering** - Coastal deployment
   - Spread crushed silicate rocks
   - Natural weathering enhances alkalinity

3. **Macroalgae/Seaweed Cultivation** - Biological approach
   - Cultivate and sink seaweed
   - Carbon sequestration via ocean floor storage

4. **Direct Ocean Capture** - Electrochemical
   - Extract CO2 directly from seawater
   - Store or utilize captured CO2

### Market Status (2026)

- **Funding:** $200M+ invested in 2024-2025
- **Projects:** 30+ pilot deployments globally
- **Challenges:** MRV accounts for 50%+ of costs
- **Regulatory:** Fragmented, no unified standards
- **Data:** "Patchwork of different frameworks"

## BGC-Argo Data Overview

### What is BGC-Argo?

- **~600 autonomous floats** measuring ocean biogeochemistry
- Profile 0-2000m depth every 10 days
- Measure: O2, pH, nitrate, chlorophyll, backscatter, irradiance
- **Data format:** NetCDF (V3.1 current standard)
- **Global coverage:** All ocean basins

### Data Structure (V3.1)

```
Core-Argo files:      Physical parameters (T, S, P)
BGC-Argo files (B-): Biogeochemical parameters
Synthetic files (S-): Combined profiles
Metadata files:       Float configuration
Trajectory files:     Position/time data
```

### Key BGC Parameters for mCDR

| Parameter | Sensor | Accuracy | mCDR Relevance |
|-----------|--------|----------|----------------|
| **pH** | ISFET or spectrophotometric | ±0.01-0.02 pH | Critical for OAE verification |
| **Dissolved O2** | Optode | ±2-3% | Ecosystem impact monitoring |
| **Nitrate** | SUNA/ISUS | ±2 μM | Nutrient perturbation |
| **Chlorophyll** | Fluorometer | ±10% | Phytoplankton response |
| **Backscatter** | Optical | Variable | Particle tracking |
| **Irradiance** | PAR sensor | ±5% | Primary production |

### Data Access

- **GDACs:** Coriolis (France), USGODAE (USA)
- **Formats:** NetCDF, CSV, Copernicus Marine format
- **APIs:** ERDDAP, OPeNDAP
- **Selection tools:** EuroArgo, ArgoVis

## mCDR MRV Data Requirements

### Current State (2026)

> "At present, given the early developmental stages of mCDR methods, **none have sufficiently robust, comprehensive MRV in place**."
> — [European Marine Board Report](https://www.marineboard.eu/publications/MRV_for_mCDR)

### Core MRV Components

**1. Carbon Removal Quantification**
- Baseline measurements
- During-deployment monitoring
- Post-deployment verification
- Long-term durability tracking (decades to centuries)

**2. Environmental Impact Assessment**
- pH changes (acidification risk)
- Ecosystem responses
- Dissolved oxygen levels
- Nutrient cycling effects

**3. Uncertainty Quantification**
- Measurement uncertainties
- Model uncertainties
- Spatial/temporal variability
- Systematic errors

### OAE-Specific Monitoring Needs

From [Carbon to Sea Initiative](https://www.carbontosea.org/mrv/):

**Required Measurements:**
- **Total Alkalinity (TA):** ±0.1-0.5% accuracy needed
- **Dissolved Inorganic Carbon (DIC)**
- **pH:** High spatial resolution
- **Salinity & Temperature:** For carbon chemistry calculations
- **pCO2:** Air-sea gas exchange rates

**Spatial Coverage:**
- Upstream baseline measurements
- Dispersion plume tracking
- Downstream impact assessment
- Regional background monitoring

**Temporal Scale:**
- Pre-deployment baseline (weeks-months)
- During deployment (continuous/high-frequency)
- Post-deployment (months-years)
- Long-term verification (decades)

### Key MRV Challenges

From [Mission Innovation CDR Report](https://mission-innovation.net/wp-content/uploads/2024/12/2024-12_CDR-Mission-MRV-Report.pdf):

1. **Cost:** MRV can be >50% of project costs
2. **Sensor Accuracy:** pH floats have "relatively large uncertainties"
3. **Autonomous TA sensors:** Still in development
4. **Data Standardization:** No unified framework
5. **Verification:** Independent third-party validation lacking
6. **Regulatory Gaps:** Fragmented global governance

## FAIR Principles for mCDR Data

### Why FAIR Matters for mCDR

1. **Carbon Credit Verification**
   - Credits require transparent, reproducible data
   - Third-party verifiers need access
   - Long-term archiving (100+ years)

2. **Regulatory Compliance**
   - EPA, London Protocol, EU regulations
   - Mandatory reporting requirements
   - Audit trails needed

3. **Scientific Credibility**
   - Peer review of MRV approaches
   - Method validation and comparison
   - Community acceptance

4. **Cost Reduction**
   - Automated data processing
   - Reduce manual QA/QC
   - Reuse existing datasets

### FAIR Score Target for mCDR

**Minimum for Carbon Credits:** 90+/100 (Grade A)
- Findable: Unique DOIs, metadata registries
- Accessible: Public APIs, long-term archives
- Interoperable: CF conventions, standard units
- Reusable: Clear provenance, quality flags

### Current BGC-Argo FAIR Gaps

Based on OOI experience, likely issues:

1. **Missing Metadata**
   - Incomplete sensor calibration histories
   - Sparse documentation of processing steps
   - Limited provenance information

2. **CF Compliance**
   - Inconsistent variable naming
   - Missing standard_name attributes
   - Incomplete coordinate metadata

3. **Quality Control**
   - Variable QC flag implementations
   - Insufficient uncertainty quantification
   - Limited metadata on QC procedures

4. **Accessibility**
   - Multiple data centers with inconsistent APIs
   - No standardized carbon chemistry products
   - Limited derived parameter availability

## Adaptation Strategy: FAIR Pipeline → mCDR-FAIR Pipeline

### Phase 1: Assess BGC-Argo Data Quality

**Tasks:**
1. Download sample BGC-Argo profiles (pH, O2, nitrate)
2. Run existing FAIRAssessor on BGC-Argo NetCDF files
3. Identify specific FAIR gaps vs OOI data
4. Document BGC-Argo data model differences

**Expected Findings:**
- Similar CF compliance issues
- Different variable naming conventions
- Additional metadata requirements for carbon chemistry

### Phase 2: Extend Enrichment for BGC Parameters

**New Enrichers Needed:**

1. **CarbonChemistryEnricher**
   - Add SOCAT/GLODAP standard names
   - Include uncertainty attributes
   - Add carbon system calculation metadata
   - Document calibration procedures

2. **SensorCalibrationEnricher**
   - Extract calibration dates from metadata
   - Add sensor serial numbers
   - Document drift corrections
   - Link to manufacturer specs

3. **UncertaintyEnricher**
   - Add measurement uncertainties
   - Propagate errors through calculations
   - Include systematic error estimates
   - Document uncertainty methodology

4. **ProvenanceEnricher** (Enhanced)
   - Full processing chain documentation
   - Software version tracking
   - Calibration file references
   - Data quality flags interpretation

### Phase 3: OAE-Specific Extensions

**For OAE monitoring projects:**

1. **Alkalinity Perturbation Tracking**
   - Baseline vs. enhanced measurements
   - Spatial dispersion modeling
   - Temporal evolution tracking

2. **Carbon Removal Accounting**
   - Calculate net CO2 removal
   - Quantify air-sea gas exchange
   - Estimate sequestration efficiency
   - Compute carbon credits (tCO2)

3. **Environmental Impact Metrics**
   - pH change quantification
   - Ecosystem indicator calculations
   - Compliance with regulatory thresholds
   - Risk assessment metrics

4. **MRV Report Generation**
   - Standardized carbon accounting reports
   - Verification-ready data packages
   - Regulatory submission formats
   - Auditable data lineage

### Phase 4: Integration & Deployment

**Data Sources:**
- BGC-Argo GDAC feeds
- OAE project monitoring buoys
- Shipboard measurements
- Satellite observations (SST, chl-a)

**Outputs:**
- FAIR-compliant NetCDF files
- Carbon removal quantification
- MRV reports (JSON/PDF)
- Dashboard visualizations

**Users:**
- mCDR companies (Vycarb, Vesta, etc.)
- Carbon credit verifiers
- Regulatory agencies
- Research institutions

## Technical Requirements

### Additional Python Packages

```python
# Carbon chemistry calculations
PyCO2SYS       # Seawater CO2 system calculations
cbsyst         # Alternative CO2 system solver

# Uncertainty propagation
uncertainties  # Error propagation
pint          # Unit handling with uncertainties

# Standards and vocabularies
cf_xarray     # Enhanced CF convention support
pyessv        # Controlled vocabulary tools
```

### Data Standards to Support

1. **CF Conventions** (existing)
2. **ACDD** (existing)
3. **SOCAT standards** - Surface Ocean CO2 Atlas
4. **GLODAP** - Global Ocean Data Analysis Project
5. **CDR-MRV Protocol** (emerging standards)

### New Metrics Beyond FAIR

**MRV-Specific Scoring:**
- Calibration completeness (20 pts)
- Uncertainty documentation (20 pts)
- Provenance traceability (20 pts)
- Verification readiness (20 pts)
- Regulatory compliance (20 pts)

**Total Score:** FAIR (100) + MRV (100) = 200 points

## Market Opportunity

### Value Proposition

**For mCDR Companies:**
- Reduce MRV costs from 50% to <20%
- Faster carbon credit issuance
- Higher credibility with verifiers
- Automated regulatory reporting

**For Verifiers:**
- Standardized data formats
- Transparent processing chains
- Reproducible calculations
- Reduced verification time/cost

**For Research Community:**
- High-quality public datasets
- Method comparison and validation
- Reproducible science
- Faster innovation cycles

### Potential Business Model

1. **Open-source core** (maintain FAIR pipeline)
2. **mCDR-MRV extensions** (premium features)
3. **Hosted service** (SaaS for mCDR companies)
4. **Consulting** (custom MRV implementations)
5. **Training/workshops** (mCDR data management)

### Funding Opportunities

- **DOE ARPA-E:** mCDR technology development
- **NSF:** Ocean observing cyberinfrastructure
- **NOAA:** Ocean acidification monitoring
- **Stripe Climate:** Technology purchases
- **Frontier Climate:** Advanced market commitments
- **Carbon removal companies:** Direct contracts

## Next Steps

### Immediate (Sprint 4A)

1. **Download BGC-Argo data** (5-10 floats with pH sensors)
2. **Run existing FAIR assessment** on BGC-Argo files
3. **Document differences** from OOI data structure
4. **Prototype carbon chemistry enricher**

### Short-term (1-2 months)

1. **Extend pipeline for BGC-Argo**
2. **Add uncertainty propagation**
3. **Implement carbon removal calculations**
4. **Create MRV report templates**

### Medium-term (3-6 months)

1. **Partner with mCDR company** (pilot project)
2. **Validate on OAE monitoring data**
3. **Develop verification workflow**
4. **Publish methodology paper**

### Long-term (6-12 months)

1. **Launch mCDR-MRV SaaS platform**
2. **Integrate with carbon registries**
3. **Pursue regulatory approval**
4. **Scale to multiple mCDR methods**

## Key Contacts & Resources

### Organizations
- [Biogeochemical Argo Program](https://biogeochemical-argo.org/)
- [Carbon to Sea Initiative](https://www.carbontosea.org/) - OAE MRV focus
- [Ocean Visions](https://oceanvisions.org/) - mCDR road-mapping
- [CarbonPlan](https://carbonplan.org/) - CDR evaluation
- [Frontier Climate](https://frontierclimate.com/) - Advanced market commitments

### Data Sources
- [Argo GDAC](https://www.seanoe.org/data/00311/42182/) - Global Data Assembly Centers
- [EuroArgo Selection Tool](https://biogeochemical-argo.org/data-access.php)
- ArgoVis - Visualization and data access
- SOCAT - Surface Ocean CO2 Atlas
- GLODAP - Interior ocean carbon data

### Key Papers & Reports
- [Mission Innovation MRV Report (2024)](https://mission-innovation.net/wp-content/uploads/2024/12/2024-12_CDR-Mission-MRV-Report.pdf)
- [European Marine Board MRV for mCDR (2025)](https://www.marineboard.eu/publications/MRV_for_mCDR)
- [Climate Law Blog: mCDR MRV 101](https://blogs.law.columbia.edu/climatechange/2025/09/12/marine-carbon-dioxide-removal-mrv-101/)

## Conclusion

**This is a high-impact opportunity.** MRV is the critical bottleneck for scaling marine CDR, and your FAIR pipeline is well-positioned to address it.

**Key Advantages:**
- Proven technology (Sprints 1-3 complete)
- Addresses $100M+ pain point (MRV costs)
- Large potential market (30+ companies)
- Strong scientific foundation
- Regulatory alignment (FAIR = verification-ready)

**Recommendation:** Pivot the project toward mCDR-MRV as primary use case, starting with BGC-Argo data quality assessment.

---

**Sources:**
- [Biogeochemical Argo Data Access](https://biogeochemical-argo.org/data-access.php)
- [Argo Float Data and Metadata from GDAC](https://www.seanoe.org/data/00311/42182/)
- [Mission Innovation MRV Report](https://mission-innovation.net/wp-content/uploads/2024/12/2024-12_CDR-Mission-MRV-Report.pdf)
- [Carbon to Sea Initiative - OAE MRV](https://www.carbontosea.org/mrv/)
- [Climate Law Blog - mCDR MRV 101](https://blogs.law.columbia.edu/climatechange/2025/09/12/marine-carbon-dioxide-removal-mrv-101/)
- [European Marine Board - MRV for mCDR](https://www.marineboard.eu/publications/MRV_for_mCDR)
- [Ocean Visions - Ocean Alkalinity Enhancement](https://oceanvisions.org/ocean-alkalinity-enhancement/)
- [ACS Sensors - Autonomous TA Sensor](https://pubs.acs.org/doi/10.1021/acssensors.4c02349)
- [Copernicus Marine - MRV for OAE](https://sp.copernicus.org/articles/2-oae2023/12/2023/)
