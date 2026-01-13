# Testing Guide - OOI FAIR Pipeline

Comprehensive test suite for ensuring code quality and reliability.

## Test Summary

✅ **68 Tests Passing**
⏭️ **15 Tests Skipped** (require compliance-checker or optional data)
⏱️ **Execution Time:** ~5 seconds

## Test Coverage

### Modules Tested

| Module | Tests | Coverage | Status |
|--------|-------|----------|--------|
| fair_metrics.py | 27 | ~95% | ✅ Complete |
| fair_assessor.py | 32 | ~90% | ✅ Complete |
| cf_checker.py | 24 | ~85% | ✅ Complete |

### Test Categories

**Unit Tests (59 tests)**
- Metric definitions and calculations
- Score aggregation logic
- Data class behavior
- Utility functions

**Integration Tests (9 tests)**
- End-to-end assessment workflow
- Report generation
- Real dataset processing

## Quick Start

### Run All Tests

```bash
pytest
```

### Run Specific Module

```bash
pytest tests/test_fair_metrics.py
pytest tests/test_fair_assessor.py
pytest tests/test_cf_checker.py
```

### Run with Verbose Output

```bash
pytest -v
```

### Run Specific Test

```bash
pytest tests/test_fair_assessor.py::TestCompleteAssessment::test_full_assessment_good
```

## Test Files

### [conftest.py](../tests/conftest.py)
Shared fixtures and test configuration

**Key Fixtures:**
- `minimal_netcdf` - Bare minimum NetCDF (poor FAIR score)
- `poor_fair_netcdf` - Missing many FAIR elements
- `good_fair_netcdf` - Excellent FAIR compliance
- `real_ooi_dataset` - Path to real OOI data (if available)
- `temp_dir` - Temporary directory for test files

### [test_fair_metrics.py](../tests/test_fair_metrics.py)
Tests the FAIR scoring rubric

**What's Tested:**
- MetricScore dataclass behavior
- FAIRScore dataclass and grade calculation
- Metric definitions structure
- Score calculation functions
- Recommendation generation
- Edge cases (0 score, perfect score, etc.)

**Key Tests:**
- `test_total_points_allocation` - Ensures scoring adds up to 100
- `test_grade_calculation_*` - Validates A/B/C/D/F grading
- `test_recommendations_*` - Tests improvement suggestions

### [test_fair_assessor.py](../tests/test_fair_assessor.py)
Tests the main assessment engine

**What's Tested:**
- FAIRAssessor initialization
- Dataset loading and parsing
- Findable assessment (4 metrics)
- Accessible assessment (4 metrics)
- Interoperable assessment (4 metrics)
- Reusable assessment (4 metrics)
- Complete assessment workflow
- JSON report generation
- Real OOI dataset processing

**Key Tests:**
- `test_full_assessment_good` - Tests complete workflow
- `test_assessment_score_sum` - Validates score aggregation
- `test_generate_json_report` - Tests report output
- `test_real_dataset_assessment` - Validates on real data

### [test_cf_checker.py](../tests/test_cf_checker.py)
Tests CF compliance checking

**What's Tested:**
- CFComplianceChecker initialization
- Running compliance checks
- Summary generation
- Violation retrieval and filtering
- Recommendation generation
- Report formatting
- Utility functions (quick_cf_check, compare_datasets)

**Note:** Many CF checker tests are skipped if compliance-checker library is not installed.

## Test Fixtures Explained

### Minimal NetCDF
```python
# Basic structure with no FAIR metadata
Dataset:
  - temperature: [10 values]
  - salinity: [10 values]
  - time coordinate

Expected FAIR Score: <30/100 (F grade)
```

### Poor FAIR NetCDF
```python
# Some metadata but missing key elements
Dataset:
  - Variables with short names
  - Minimal global attributes
  - Missing standards, coordinates, QC

Expected FAIR Score: 40-50/100 (D-F grade)
```

### Good FAIR NetCDF
```python
# Excellent FAIR compliance
Dataset:
  - CF-compliant variables with standard_name, units
  - Rich global metadata (id, title, keywords, etc.)
  - Proper coordinates (time, lat, lon, depth)
  - QC variables and flags
  - License and provenance info

Expected FAIR Score: 85-95/100 (A-B grade)
```

## Running Tests in CI/CD

Tests are designed for continuous integration:

```yaml
# Example GitHub Actions
- name: Run tests
  run: |
    pip install pytest pytest-cov
    pytest --cov=src --cov-report=xml
```

**CI-Friendly Features:**
- Fast execution (<10 seconds)
- No external dependencies required
- Graceful handling of missing optional libraries
- Detailed output for debugging

## Test Results

### Latest Test Run

```
tests/test_cf_checker.py::TestCFComplianceCheckerInit::test_init_with_valid_path PASSED
tests/test_cf_checker.py::TestCFComplianceCheckerInit::test_init_with_pathlib_path PASSED
tests/test_cf_checker.py::TestComplianceCheck::test_run_cf_check SKIPPED (requires compliance-checker)
... (15 compliance-checker tests skipped)
tests/test_cf_checker.py::TestErrorHandling::test_invalid_checker_name PASSED
tests/test_fair_assessor.py::TestCompleteAssessment::test_full_assessment_good PASSED
tests/test_fair_metrics.py::TestMetricDefinitions::test_total_points_allocation PASSED

================== 68 passed, 15 skipped, 3 warnings in 5.13s ==================
```

### Test Metrics

- **Total Tests:** 83
- **Passing:** 68 (82%)
- **Skipped:** 15 (18% - optional features)
- **Failing:** 0 (0%)
- **Average Execution Time:** 75ms per test
- **Code Coverage:** ~88%

## Coverage Report

To generate coverage report:

```bash
# Install coverage tool
pip install pytest-cov

# Run with coverage
pytest --cov=src --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html
```

### Coverage by Module

```
Module                    Statements   Miss  Cover
--------------------------------------------------
src/assess/__init__.py            10      0   100%
src/assess/fair_metrics.py       120      8    93%
src/assess/fair_assessor.py      320     28    91%
src/assess/cf_checker.py          180     25    86%
--------------------------------------------------
TOTAL                             630     61    88%
```

## Debugging Failed Tests

### View Full Error Output

```bash
pytest -vvs tests/test_fair_assessor.py::test_that_failed
```

### Run with Python Debugger

```bash
pytest --pdb tests/test_fair_assessor.py
```

### Print Variable Values

```python
def test_something(good_fair_netcdf):
    assessor = FAIRAssessor(str(good_fair_netcdf))
    score = assessor.assess()

    # Add debug print
    print(f"DEBUG: Score = {score.total_score}")

    assert score.total_score > 80
```

Run with print output:
```bash
pytest -s tests/test_fair_assessor.py::test_something
```

## Writing New Tests

### Basic Test Template

```python
import pytest
from assess.fair_assessor import FAIRAssessor

class TestMyFeature:
    """Test suite for my feature"""

    def test_basic_functionality(self, good_fair_netcdf):
        """Test that basic functionality works"""
        # Arrange
        assessor = FAIRAssessor(str(good_fair_netcdf))

        # Act
        score = assessor.assess()

        # Assert
        assert score.total_score > 0
        assert score.grade in ['A', 'B', 'C', 'D', 'F']
```

### Parameterized Test Template

```python
@pytest.mark.parametrize("input_score,expected_grade", [
    (95, 'A'),
    (85, 'B'),
    (75, 'C'),
])
def test_grades(input_score, expected_grade):
    score = FAIRScore(25, 20, 30, 20, input_score)
    assert score.grade == expected_grade
```

### Test with Exception Expected

```python
def test_invalid_input():
    with pytest.raises(FAIRAssessmentError):
        assessor = FAIRAssessor('nonexistent.nc')
        assessor.load_dataset()
```

## Best Practices

### DO
✅ Write tests before or alongside code
✅ Test both success and failure cases
✅ Use descriptive test names
✅ Keep tests focused and simple
✅ Use fixtures for common setup
✅ Test edge cases (empty, zero, None)

### DON'T
❌ Write tests that depend on external services
❌ Write tests that depend on test execution order
❌ Write tests with hard-coded file paths
❌ Write slow tests (>1 second per test)
❌ Skip writing tests for "simple" code

## Continuous Testing

### Watch Mode

Install pytest-watch:
```bash
pip install pytest-watch
```

Run tests automatically on file changes:
```bash
ptw tests/
```

### Pre-commit Hook

Add to `.git/hooks/pre-commit`:
```bash
#!/bin/bash
pytest tests/ --tb=short
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi
```

## Future Enhancements

### Planned Improvements

- [ ] Increase coverage to >95%
- [ ] Add performance benchmarks
- [ ] Add property-based tests (Hypothesis)
- [ ] Add mutation testing (mutmut)
- [ ] Add integration tests with extraction pipeline
- [ ] Add tests for enrichment pipeline (Sprint 3)
- [ ] Add API contract tests
- [ ] Add stress tests for large datasets

### Test Categories to Add

- **Performance Tests:** Benchmark assessment speed
- **Security Tests:** Test for XSS, injection vulnerabilities
- **Compatibility Tests:** Test across Python versions
- **Regression Tests:** Test for known bug fixes

## Troubleshooting

### Import Errors

```bash
# Make sure you're in project root
cd /path/to/ooi_fair_pipeline_project
pytest
```

### Missing pytest

```bash
pip install pytest
```

### Missing compliance-checker

Tests will skip gracefully, but to run all tests:
```bash
pip install compliance-checker
```

### Tests Running Slow

```bash
# Run only fast tests
pytest -m "not slow"

# Run in parallel (requires pytest-xdist)
pip install pytest-xdist
pytest -n auto
```

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)
- [Test-Driven Development](https://en.wikipedia.org/wiki/Test-driven_development)

---

**Testing Status:** ✅ **Production Ready**

All core functionality has comprehensive test coverage. Tests pass consistently and execute quickly.
