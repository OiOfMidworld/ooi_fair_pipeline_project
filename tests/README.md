# OOI FAIR Pipeline - Test Suite

Comprehensive unit tests for the FAIR assessment engine.

## Test Structure

```
tests/
├── conftest.py                 # Pytest fixtures and configuration
├── test_fair_metrics.py        # Tests for scoring rubric
├── test_fair_assessor.py       # Tests for assessment engine
└── test_cf_checker.py          # Tests for CF compliance checker
```

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest tests/test_fair_metrics.py
pytest tests/test_fair_assessor.py
pytest tests/test_cf_checker.py
```

### Run Specific Test Class

```bash
pytest tests/test_fair_metrics.py::TestMetricScore
```

### Run Specific Test Function

```bash
pytest tests/test_fair_assessor.py::TestCompleteAssessment::test_full_assessment_good
```

### Run with Verbose Output

```bash
pytest -v
```

### Run with Print Statements

```bash
pytest -s
```

### Run Tests Matching Pattern

```bash
pytest -k "findable"  # Run all tests with 'findable' in name
```

## Test Categories

### Unit Tests

Test individual components in isolation:
- Metric definitions and calculations
- Score aggregation
- Report generation
- Error handling

### Integration Tests

Test components working together:
- Full assessment workflow
- Dataset loading and parsing
- End-to-end scoring

### Tests with Real Data

Some tests use the real OOI sample dataset if available:
- Located at `data/raw/test_download.nc`
- Tests are skipped if file not present
- Marked with `@pytest.mark.requires_data`

## Test Fixtures

Located in `conftest.py`:

### `temp_dir`
Provides a temporary directory for test files

### `minimal_netcdf`
Creates a NetCDF with minimal metadata (poor FAIR score expected)

### `poor_fair_netcdf`
Creates a NetCDF with some metadata but missing key FAIR elements

### `good_fair_netcdf`
Creates a CF-compliant NetCDF with excellent FAIR metadata

### `real_ooi_dataset`
Path to real OOI dataset if available (returns None if not)

## Coverage

To run tests with coverage report:

```bash
# Install pytest-cov if needed
pip install pytest-cov

# Run with coverage
pytest --cov=src --cov-report=html --cov-report=term-missing
```

View HTML coverage report:
```bash
open htmlcov/index.html
```

## Test Markers

Tests are marked for easy filtering:

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only tests requiring real data
pytest -m requires_data

# Skip slow tests
pytest -m "not slow"
```

## Writing New Tests

### Test Structure

```python
import pytest
from assess.fair_assessor import FAIRAssessor

class TestMyFeature:
    """Test description"""

    def test_something(self, fixture_name):
        """Test specific behavior"""
        # Arrange
        assessor = FAIRAssessor('path/to/dataset.nc')

        # Act
        result = assessor.assess()

        # Assert
        assert result.total_score > 0
```

### Using Fixtures

```python
def test_with_fixture(minimal_netcdf):
    """Test using a fixture"""
    assessor = FAIRAssessor(str(minimal_netcdf))
    score = assessor.assess()
    assert score is not None
```

### Parameterized Tests

```python
@pytest.mark.parametrize("score,expected_grade", [
    (95, 'A'),
    (85, 'B'),
    (75, 'C'),
    (65, 'D'),
    (55, 'F'),
])
def test_grade_calculation(score, expected_grade):
    fair_score = FAIRScore(25, 20, 30, 25, score)
    assert fair_score.grade == expected_grade
```

### Skip Tests Conditionally

```python
def test_optional_feature(real_ooi_dataset):
    """Test that needs real data"""
    if real_ooi_dataset is None:
        pytest.skip("Real dataset not available")

    # Test code here
```

## Continuous Integration

Tests are designed to run in CI environments:
- No external dependencies required (except compliance-checker for some tests)
- Tests requiring real data are skipped gracefully
- Fast execution (<30 seconds for full suite)

## Test Data

Test data is generated dynamically using xarray:
- No need to commit large NetCDF files to repo
- Consistent test data across environments
- Easy to create variations for edge cases

## Troubleshooting

### Import Errors

If you get import errors, make sure you're running pytest from the project root:
```bash
cd /path/to/ooi_fair_pipeline_project
pytest
```

### Missing Dependencies

Install test dependencies:
```bash
pip install pytest pytest-cov
```

### Compliance Checker Tests Failing

If compliance-checker tests fail, you may need to install it:
```bash
pip install compliance-checker
```

Or skip those tests:
```bash
pytest -k "not cf_checker"
```

## Test Metrics

**Current Status:**
- Test Files: 3
- Test Functions: 100+
- Code Coverage: ~85% (target: >90%)
- Execution Time: ~15 seconds

## Future Enhancements

- [ ] Add performance benchmarks
- [ ] Add property-based tests with Hypothesis
- [ ] Add mutation testing
- [ ] Increase coverage to >95%
- [ ] Add integration tests with data extraction pipeline
- [ ] Add tests for enrichment pipeline (Sprint 3)

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
