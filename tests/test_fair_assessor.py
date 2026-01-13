"""
Unit tests for FAIR Assessor

Tests the main assessment engine including dataset loading,
metric evaluation, and report generation.
"""

import pytest
import json
from pathlib import Path

from assess.fair_assessor import FAIRAssessor
from assess.fair_metrics import FAIRScore, MetricScore
from utils.exceptions import FAIRAssessmentError


class TestFAIRAssessorInit:
    """Test FAIRAssessor initialization"""

    def test_init_with_valid_path(self, minimal_netcdf):
        """Test initialization with valid dataset path"""
        assessor = FAIRAssessor(str(minimal_netcdf))

        assert assessor.dataset_path == minimal_netcdf
        assert assessor.dataset is None  # Not loaded yet
        assert assessor.global_attrs == {}
        assert assessor.variables == {}

    def test_init_with_pathlib_path(self, minimal_netcdf):
        """Test initialization with Path object"""
        assessor = FAIRAssessor(minimal_netcdf)
        assert isinstance(assessor.dataset_path, Path)


class TestDatasetLoading:
    """Test dataset loading functionality"""

    def test_load_minimal_dataset(self, minimal_netcdf):
        """Test loading a minimal NetCDF file"""
        assessor = FAIRAssessor(str(minimal_netcdf))
        assessor.load_dataset()

        assert assessor.dataset is not None
        assert isinstance(assessor.global_attrs, dict)
        assert isinstance(assessor.variables, dict)
        assert len(assessor.variables) >= 2  # temp and salinity

    def test_load_nonexistent_file(self, temp_dir):
        """Test loading a file that doesn't exist"""
        fake_path = temp_dir / 'nonexistent.nc'
        assessor = FAIRAssessor(str(fake_path))

        with pytest.raises(FAIRAssessmentError):
            assessor.load_dataset()

    def test_extract_global_attributes(self, good_fair_netcdf):
        """Test that global attributes are extracted correctly"""
        assessor = FAIRAssessor(str(good_fair_netcdf))
        assessor.load_dataset()

        # Check that key attributes are present
        assert 'title' in assessor.global_attrs
        assert 'Conventions' in assessor.global_attrs
        assert assessor.global_attrs['title'] == 'Test Ocean Dataset'

    def test_extract_variable_attributes(self, good_fair_netcdf):
        """Test that variable attributes are extracted correctly"""
        assessor = FAIRAssessor(str(good_fair_netcdf))
        assessor.load_dataset()

        # Check variable attributes
        assert 'sea_water_temperature' in assessor.variables
        var_attrs = assessor.variables['sea_water_temperature']
        assert 'standard_name' in var_attrs
        assert 'units' in var_attrs
        assert var_attrs['units'] == 'degree_C'


class TestFindableAssessment:
    """Test Findability (F) assessment"""

    def test_assess_findable_minimal(self, minimal_netcdf):
        """Test findable assessment on minimal dataset"""
        assessor = FAIRAssessor(str(minimal_netcdf))
        assessor.load_dataset()

        scores = assessor.assess_findable()

        assert isinstance(scores, list)
        assert len(scores) == 4  # 4 findable metrics
        assert all(isinstance(s, MetricScore) for s in scores)

        # Minimal dataset should have low scores
        total_earned = sum(s.points_earned for s in scores)
        assert total_earned < 15  # Less than 60% of 25 points

    def test_assess_findable_good(self, good_fair_netcdf):
        """Test findable assessment on good dataset"""
        assessor = FAIRAssessor(str(good_fair_netcdf))
        assessor.load_dataset()

        scores = assessor.assess_findable()

        # Good dataset should score high
        total_earned = sum(s.points_earned for s in scores)
        assert total_earned > 20  # More than 80% of 25 points

    def test_findable_unique_identifier(self, good_fair_netcdf):
        """Test unique identifier metric specifically"""
        assessor = FAIRAssessor(str(good_fair_netcdf))
        assessor.load_dataset()

        scores = assessor.assess_findable()
        id_score = next(s for s in scores if s.name == 'unique_identifier')

        assert id_score.points_earned == 5  # Should be perfect
        assert id_score.status == 'pass'


class TestAccessibleAssessment:
    """Test Accessibility (A) assessment"""

    def test_assess_accessible_minimal(self, minimal_netcdf):
        """Test accessible assessment on minimal dataset"""
        assessor = FAIRAssessor(str(minimal_netcdf))
        assessor.load_dataset()

        scores = assessor.assess_accessible()

        assert isinstance(scores, list)
        assert len(scores) == 4  # 4 accessible metrics

        # Minimal dataset should score low
        total_earned = sum(s.points_earned for s in scores)
        assert total_earned < 12  # Less than 60% of 20 points

    def test_assess_accessible_good(self, good_fair_netcdf):
        """Test accessible assessment on good dataset"""
        assessor = FAIRAssessor(str(good_fair_netcdf))
        assessor.load_dataset()

        scores = assessor.assess_accessible()

        # Good dataset should score high
        total_earned = sum(s.points_earned for s in scores)
        assert total_earned > 16  # More than 80% of 20 points


class TestInteroperableAssessment:
    """Test Interoperability (I) assessment"""

    def test_assess_interoperable_minimal(self, minimal_netcdf):
        """Test interoperable assessment on minimal dataset"""
        assessor = FAIRAssessor(str(minimal_netcdf))
        assessor.load_dataset()

        scores = assessor.assess_interoperable()

        assert isinstance(scores, list)
        assert len(scores) == 4  # 4 interoperable metrics

        # Check CF compliance score exists
        cf_score = next(s for s in scores if s.name == 'cf_compliance')
        assert cf_score is not None

    def test_assess_interoperable_good(self, good_fair_netcdf):
        """Test interoperable assessment on good dataset"""
        assessor = FAIRAssessor(str(good_fair_netcdf))
        assessor.load_dataset()

        scores = assessor.assess_interoperable()

        # Good dataset should score reasonably high
        total_earned = sum(s.points_earned for s in scores)
        assert total_earned > 20  # More than 67% of 30 points

    def test_data_format_check(self, good_fair_netcdf):
        """Test data format is correctly identified"""
        assessor = FAIRAssessor(str(good_fair_netcdf))
        assessor.load_dataset()

        scores = assessor.assess_interoperable()
        format_score = next(s for s in scores if s.name == 'data_format')

        assert format_score.points_earned == 5  # NetCDF gets full points
        assert format_score.status == 'pass'

    def test_coordinate_system_evaluation(self, good_fair_netcdf):
        """Test coordinate system detection"""
        assessor = FAIRAssessor(str(good_fair_netcdf))
        assessor.load_dataset()

        scores = assessor.assess_interoperable()
        coord_score = next(s for s in scores if s.name == 'coordinate_system')

        # Good dataset has time, lat, lon, depth
        assert coord_score.points_earned >= 4  # Most coords present


class TestReusableAssessment:
    """Test Reusability (R) assessment"""

    def test_assess_reusable_minimal(self, minimal_netcdf):
        """Test reusable assessment on minimal dataset"""
        assessor = FAIRAssessor(str(minimal_netcdf))
        assessor.load_dataset()

        scores = assessor.assess_reusable()

        assert isinstance(scores, list)
        assert len(scores) == 4  # 4 reusable metrics

    def test_assess_reusable_good(self, good_fair_netcdf):
        """Test reusable assessment on good dataset"""
        assessor = FAIRAssessor(str(good_fair_netcdf))
        assessor.load_dataset()

        scores = assessor.assess_reusable()

        # Good dataset should score high
        total_earned = sum(s.points_earned for s in scores)
        assert total_earned > 20  # More than 80% of 25 points

    def test_license_check(self, good_fair_netcdf):
        """Test license detection"""
        assessor = FAIRAssessor(str(good_fair_netcdf))
        assessor.load_dataset()

        scores = assessor.assess_reusable()
        license_score = next(s for s in scores if s.name == 'clear_license')

        assert license_score.points_earned == 5  # Has license
        assert license_score.status == 'pass'

    def test_quality_control_evaluation(self, good_fair_netcdf):
        """Test QC variable detection"""
        assessor = FAIRAssessor(str(good_fair_netcdf))
        assessor.load_dataset()

        scores = assessor.assess_reusable()
        qc_score = next(s for s in scores if s.name == 'quality_control')

        # Good dataset has QC variables
        assert qc_score.points_earned > 0


class TestCompleteAssessment:
    """Test complete FAIR assessment workflow"""

    def test_full_assessment_minimal(self, minimal_netcdf):
        """Test complete assessment on minimal dataset"""
        assessor = FAIRAssessor(str(minimal_netcdf))
        score = assessor.assess()

        assert isinstance(score, FAIRScore)
        assert score.total_score < 50  # Poor score expected
        assert score.grade in ['D', 'F']

        # Check all components are present
        assert len(score.findable_details) == 4
        assert len(score.accessible_details) == 4
        assert len(score.interoperable_details) == 4
        assert len(score.reusable_details) == 4

    def test_full_assessment_good(self, good_fair_netcdf):
        """Test complete assessment on good dataset"""
        assessor = FAIRAssessor(str(good_fair_netcdf))
        score = assessor.assess()

        assert isinstance(score, FAIRScore)
        assert score.total_score > 80  # Good score expected
        assert score.grade in ['A', 'B']

    def test_assessment_score_sum(self, good_fair_netcdf):
        """Test that component scores sum to total"""
        assessor = FAIRAssessor(str(good_fair_netcdf))
        score = assessor.assess()

        calculated_total = (
            score.findable_score +
            score.accessible_score +
            score.interoperable_score +
            score.reusable_score
        )

        assert abs(calculated_total - score.total_score) < 0.1

    def test_assessment_without_load_calls_load(self, minimal_netcdf):
        """Test that assess() calls load_dataset() if needed"""
        assessor = FAIRAssessor(str(minimal_netcdf))

        # Don't call load_dataset() explicitly
        score = assessor.assess()

        # Should still work - dataset should be loaded
        assert assessor.dataset is not None
        assert isinstance(score, FAIRScore)


class TestReportGeneration:
    """Test report generation functionality"""

    def test_generate_json_report(self, good_fair_netcdf, temp_dir):
        """Test generating a JSON report"""
        assessor = FAIRAssessor(str(good_fair_netcdf))
        score = assessor.assess()

        output_path = temp_dir / 'test_report.json'
        result_path = assessor.generate_report(score, output_path=str(output_path))

        assert Path(result_path).exists()

        # Verify JSON structure
        with open(output_path) as f:
            report = json.load(f)

        assert 'dataset' in report
        assert 'summary' in report
        assert 'details' in report
        assert 'recommendations' in report

    def test_report_summary_content(self, good_fair_netcdf, temp_dir):
        """Test report summary contains correct information"""
        assessor = FAIRAssessor(str(good_fair_netcdf))
        score = assessor.assess()

        output_path = temp_dir / 'test_report.json'
        assessor.generate_report(score, output_path=str(output_path))

        with open(output_path) as f:
            report = json.load(f)

        summary = report['summary']
        assert 'total_score' in summary
        assert 'grade' in summary
        assert 'findable' in summary
        assert 'accessible' in summary
        assert 'interoperable' in summary
        assert 'reusable' in summary

        assert summary['grade'] in ['A', 'B', 'C', 'D', 'F']

    def test_report_details_structure(self, good_fair_netcdf, temp_dir):
        """Test report details have correct structure"""
        assessor = FAIRAssessor(str(good_fair_netcdf))
        score = assessor.assess()

        output_path = temp_dir / 'test_report.json'
        assessor.generate_report(score, output_path=str(output_path))

        with open(output_path) as f:
            report = json.load(f)

        details = report['details']

        # Check all FAIR components
        assert 'findable' in details
        assert 'accessible' in details
        assert 'interoperable' in details
        assert 'reusable' in details

        # Check metric structure
        for metric in details['findable']:
            assert 'name' in metric
            assert 'points_earned' in metric
            assert 'points_possible' in metric
            assert 'status' in metric

    def test_report_recommendations(self, poor_fair_netcdf, temp_dir):
        """Test report includes recommendations"""
        assessor = FAIRAssessor(str(poor_fair_netcdf))
        score = assessor.assess()

        output_path = temp_dir / 'test_report.json'
        assessor.generate_report(score, output_path=str(output_path))

        with open(output_path) as f:
            report = json.load(f)

        recommendations = report['recommendations']

        # Poor dataset should have recommendations
        assert len(recommendations) > 0

        for rec in recommendations:
            assert 'priority' in rec
            assert 'category' in rec
            assert 'items' in rec

    def test_generate_report_without_file(self, good_fair_netcdf):
        """Test generating report as JSON string"""
        assessor = FAIRAssessor(str(good_fair_netcdf))
        score = assessor.assess()

        json_string = assessor.generate_report(score, output_path=None)

        # Should return valid JSON string
        report = json.loads(json_string)
        assert 'summary' in report
        assert 'details' in report


class TestRealOOIDataset:
    """Test with real OOI dataset if available"""

    def test_real_dataset_assessment(self, real_ooi_dataset):
        """Test assessment on real OOI dataset"""
        if real_ooi_dataset is None:
            pytest.skip("Real OOI dataset not available")

        assessor = FAIRAssessor(str(real_ooi_dataset))
        score = assessor.assess()

        # Real OOI data should score reasonably well
        assert isinstance(score, FAIRScore)
        assert score.total_score > 50  # At least D grade

        # Log the score for info
        print(f"\nReal OOI Dataset Score: {score.total_score:.1f}/100 (Grade: {score.grade})")

    def test_real_dataset_has_all_components(self, real_ooi_dataset):
        """Test that real dataset assessment has all components"""
        if real_ooi_dataset is None:
            pytest.skip("Real OOI dataset not available")

        assessor = FAIRAssessor(str(real_ooi_dataset))
        score = assessor.assess()

        assert len(score.findable_details) > 0
        assert len(score.accessible_details) > 0
        assert len(score.interoperable_details) > 0
        assert len(score.reusable_details) > 0


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_attributes(self, minimal_netcdf):
        """Test handling dataset with minimal attributes"""
        assessor = FAIRAssessor(str(minimal_netcdf))
        assessor.load_dataset()

        # Should not crash even with minimal metadata
        scores = assessor.assess_findable()
        assert isinstance(scores, list)

    def test_no_variables(self, temp_dir):
        """Test handling dataset with no data variables"""
        import xarray as xr
        import numpy as np

        # Create dataset with only coords, no data vars
        data = xr.Dataset(
            coords={'time': np.arange(10)}
        )
        file_path = temp_dir / 'no_vars.nc'
        data.to_netcdf(file_path)

        assessor = FAIRAssessor(str(file_path))
        assessor.load_dataset()

        # Should handle gracefully
        scores = assessor.assess_interoperable()
        assert isinstance(scores, list)
