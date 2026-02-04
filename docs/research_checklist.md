# BGC-Argo MRV Research Checklist

**Total Time**: 8-10 hours  
**Goal**: Understand why your FAIR pipeline is crucial for ocean CDR verification

---

## Phase 1: Understanding the Carbon Market Problem (2 hours)

### The Credibility Crisis

- [ ] **Read: "The Voluntary Carbon Market Explained" (30 min)**
  - Link: https://www.goldstandard.org/blog-item/voluntary-carbon-market-explained
  - Focus: Why data quality = trust = money
  - Note key insights in research doc

- [ ] **Skim: Recent carbon credit scandals (30 min)**
  - Google: "carbon credit scandal 2023" or "forest carbon integrity issues"
  - Focus: Why ocean CDR is attracting investment (harder to fake)
  - Document: What went wrong with data/verification

- [ ] **Watch: Ocean CDR Verification video (20 min)**
  - Search YouTube: "Ocean Visions CDR" or "ClimateWorks ocean carbon"
  - Look for: Measurement challenges, verification bottlenecks
  - Note: Specific data quality concerns mentioned

- [ ] **Answer key question**: *Why can't we just trust the data companies provide?*
  - Write 2-3 sentences in research notes
  - Document: Perverse incentives, lack of standards, verification gaps

---

## Phase 2: Understanding BGC-Argo Data (3 hours)

### What BGC-Argo Measures and Why It Matters

- [ ] **Read: "Why BGC-Argo?" section (30 min)**
  - Link: https://biogeochemical-argo.org/
  - Document: What sensors are on floats (pH, O2, nitrate, chl, etc.)
  - Note: Why these matter for carbon cycle
  - Map: Geographic coverage

- [ ] **Explore BGC-Argo data portal (1 hour)**
  - Link: https://www.seanoe.org/data/00311/42182/
  - Task: Download 1 sample BGC-Argo profile (pH + oxygen)
  - Task: Open in Python with xarray
  - Document: What metadata IS present
  - Document: What metadata is MISSING
  - Compare: How different from OOI data?

- [ ] **Skim: BGC-Argo Quality Control Manual (1 hour)**
  - Link: https://archimer.ifremer.fr/doc/00745/85700/
  - Focus: pH and oxygen QC procedures (skip other sensors)
  - Note: QC flag meanings and completeness
  - Ask: Are QC flags FAIR-compliant? Auditable?

- [ ] **Answer key question**: *What makes BGC-Argo data hard to use for MRV?*
  - List 3-5 specific challenges in research notes
  - Examples: Inconsistent metadata, sensor drift tracking, provenance gaps

---

## Phase 3: Understanding Ocean Alkalinity Enhancement (1.5 hours)

### What OAE Is and What It Measures

- [ ] **Read: "Ocean Alkalinity Enhancement 101" (30 min)**
  - Link: https://oceanvisions.org/roadmaps/ocean-alkalinity-enhancement/
  - Understand: What it is (adding alkaline materials to seawater)
  - Understand: Why it works (CO2 + alkalinity chemistry)
  - Document: Key measurements needed (pH, alkalinity, pCO2, DIC)

- [ ] **Watch: OAE company pitch videos (30 min)**
  - Companies to check:
    - [ ] Vesta (olivine on beaches)
    - [ ] Planetary Technologies (electrochemical)
    - [ ] Ebb Carbon (electrochemical enhancement)
  - Note: What data do they claim to collect?
  - Note: How do they verify carbon removal?
  - Ask: Where are the data quality gaps?

- [ ] **Search: Recent OAE pilot results (30 min)**
  - Google Scholar: "ocean alkalinity enhancement" + "field trial" + 2024
  - Find 2-3 recent papers/reports
  - Document: What sensors did they use?
  - Document: What data challenges did they mention?

- [ ] **Answer key question**: *What measurements prove OAE worked?*
  - List specific variables and why they matter
  - Note: Baseline requirements + perturbation detection needs

---

## Phase 4: The MRV Standards Gap (1.5 hours)

### Where Your FAIR Pipeline Fits

- [ ] **Read: CDR Verification Framework (45 min)**
  - Link: https://puro.earth/carbon-removal-methods/
  - Look for: Ocean-based carbon removal methods
  - Document: What data requirements do they specify?
  - Ask: Do they mention FAIR principles? (probably not, but should)
  - Note: Gaps your pipeline could fill

- [ ] **Skim: ISO 14064 Standard Overview (30 min)**
  - Google: "ISO 14064 GHG accounting data requirements"
  - Focus: Data quality requirements, verification principles
  - Ask: Would FAIR principles satisfy these requirements?
  - Map: FAIR principles to ISO requirements

- [ ] **Find: Ocean CDR MRV Workshop Reports (15 min)**
  - Search: "Ocean CDR measurement reporting verification workshop" + 2023/2024
  - Look for: Ocean Visions, ClimateWorks Foundation reports
  - Document: What are the open challenges mentioned?
  - Highlight: Data-related challenges

- [ ] **Answer key question**: *What does "verification-grade" data look like?*
  - Map MRV requirements to FAIR principles:
    - Complete provenance → R1.2 ✓
    - Auditable QC flags → I1 ✓
    - Persistent identifiers → F1 ✓
    - Interoperable formats → I2-I3 ✓

---

## Phase 5: Competitive Landscape (30 min)

### Who Else Is Working on This?

- [ ] **Search: Ocean CDR data platforms (15 min)**
  - LinkedIn/Google: "Ocean CDR data platform"
  - LinkedIn/Google: "MRV for ocean carbon removal"
  - Check companies: [C]worthy, Isometric, Carbonplan, Sylvera
  - Document: What services do they offer?

- [ ] **Identify your niche (15 min)**
  - Note: What are competitors doing?
  - Note: What gap are you filling?
  - Write: Your differentiation (in-situ sensor data quality via FAIR)

- [ ] **Answer key question**: *What makes your approach unique?*
  - Write 2-3 sentences distinguishing your pipeline
  - Example: "Most focus on satellite/modeling, few on in-situ data quality"

---

## Research Output Deliverables

### Create Documentation

- [ ] **Create: `docs/MRV_RESEARCH_NOTES.md`**
  - Template structure provided below
  - Fill in as you complete research

- [ ] **Capture during research:**
  - [ ] 5-10 impactful quotes about data quality challenges
  - [ ] 3-5 statistics on carbon market size/growth
  - [ ] Specific requirements from verification standards
  - [ ] 5-10 contact names (researchers/companies)

- [ ] **Synthesize: Value Proposition (after all research)**
  - [ ] Problem statement (2-3 sentences)
  - [ ] How FAIR helps (bullet points)
  - [ ] Competitive differentiation (2-3 sentences)
  - [ ] Target customers (list 3-5 types)

---

## Research Notes Template

```markdown
# MRV Research Notes

## Carbon Market Context
**Key problem**:

**Why data matters**:

**Current scandals/issues**:

**Market size/opportunity**:

---

## BGC-Argo Data Characteristics
**What's measured**:

**Sensor types**:

**Current metadata gaps**:

**QC flag completeness**:

**Comparison to OOI data**:

---

## OAE Verification Requirements
**What OAE is**:

**Key measurements needed**:

**Baseline requirements**:

**Perturbation detection needs**:

**Companies/pilots reviewed**:

---

## MRV Standards
**Puro.earth requirements**:

**ISO 14064 relevant sections**:

**FAIR principle mapping**:

**Verification body expectations**:

---

## Competitive Landscape
**Existing solutions**:

**Gaps in market**:

**My differentiation**:

---

## Value Proposition
**Problem statement**:

**How FAIR helps**:

**Target customers**:

**Competitive advantage**:

---

## Useful Quotes


---

## Key Statistics


---

## Important Contacts


---

## Next Steps/Questions

```

---

## Time-Boxing Schedule

### Day 1 (3 hours)
- [ ] Complete Phase 1: Carbon Market Problem
- [ ] Complete Phase 2: BGC-Argo Data

### Day 2 (2 hours)
- [ ] Complete Phase 3: OAE Specifics

### Day 3 (2-3 hours)
- [ ] Complete Phase 4: MRV Standards
- [ ] Complete Phase 5: Competitive Landscape
- [ ] Synthesize findings in research doc

---

## Success Criteria

After completing this checklist, you should be able to:

- [ ] Explain carbon market credibility crisis in 2-3 sentences
- [ ] Describe 3-5 specific BGC-Argo data quality issues
- [ ] List key measurements needed for OAE verification
- [ ] Map FAIR principles to MRV requirements
- [ ] Articulate your unique value proposition
- [ ] Identify 3-5 potential customers/partners
- [ ] Have research notes document completed

---

**Start Date**: _______________  
**Target Completion**: _______________  
**Actual Completion**: _______________

---

## Quick Reference Links

- BGC-Argo Portal: https://biogeochemical-argo.org/
- Data Access: https://www.seanoe.org/data/00311/42182/
- Ocean Visions: https://oceanvisions.org/
- Puro.earth: https://puro.earth/
- Gold Standard: https://www.goldstandard.org/

---

**Notes/Insights as You Go**: