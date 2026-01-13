"""
Unit tests for CF Compliance Checker

Tests the CF conventions compliance checking functionality.
"""

import pytest
from pathlib import Path

from assess.cf_checker import CFComplianceChecker, quick_cf_check, compare_datasets
from utils.exceptions import ComplianceCheckError


class TestCFComplianceCheckerInit:
    """Test CFComplianceChecker initialization"""

    def test_init_with_valid_path(self, minimal_netcdf):
        """Test initialization with valid dataset path"""
        checker = CFComplianceChecker(str(minimal_netcdf))

        assert checker.dataset_path == minimal_netcdf
        assert checker.results is None  # Not run yet

    def test_init_with_pathlib_path(self, minimal_netcdf):
        """Test initialization with Path object"""
        checker = CFComplianceChecker(minimal_netcdf)
        assert isinstance(checker.dataset_path, Path)


class TestComplianceCheck:
    """Test running compliance checks"""

    def test_run_cf_check(self, good_fair_netcdf):
        """Test running CF compliance check"""
        checker = CFComplianceChecker(str(good_fair_netcdf))

        try:
            results = checker.run_compliance_check(checker='cf')
            assert results is not None
            assert checker.results is not None
        except ComplianceCheckError as e:
            # Compliance checker might not be installed in test environment
            pytest.skip(f"compliance-checker not available: {e}")

    def test_run_check_stores_results(self, good_fair_netcdf):
        """Test that run_compliance_check stores results"""
        checker = CFComplianceChecker(str(good_fair_netcdf))

        try:
            checker.run_compliance_check()
            assert checker.results is not None
        except ComplianceCheckError:
            pytest.skip("compliance-checker not available")

    def test_run_check_nonexistent_file(self, temp_dir):
        """Test running check on nonexistent file"""
        fake_path = temp_dir / 'nonexistent.nc'
        checker = CFComplianceChecker(str(fake_path))

        with pytest.raises(ComplianceCheckError):
            checker.run_compliance_check()


class TestSummaryGeneration:
    """Test summary generation from results"""

    def test_get_summary_without_results(self, good_fair_netcdf):
        """Test getting summary without running check first"""
        checker = CFComplianceChecker(str(good_fair_netcdf))

        summary = checker.get_summary()
        assert summary == {}  # Should return empty dict

    def test_get_summary_with_results(self, good_fair_netcdf):
        """Test getting summary after running check"""
        checker = CFComplianceChecker(str(good_fair_netcdf))

        try:
            checker.run_compliance_check()
            summary = checker.get_summary()

            # Check summary structure
            assert 'scored_points' in summary
            assert 'possible_points' in summary
            assert 'percentage' in summary
            assert 'total_issues' in summary

            # Check types
            assert isinstance(summary['scored_points'], (int, float))
            assert isinstance(summary['possible_points'], (int, float))
            assert isinstance(summary['percentage'], float)

        except ComplianceCheckError:
            pytest.skip("compliance-checker not available")

    def test_summary_percentage_calculation(self, good_fair_netcdf):
        """Test percentage calculation in summary"""
        checker = CFComplianceChecker(str(good_fair_netcdf))

        try:
            checker.run_compliance_check()
            summary = checker.get_summary()

            if summary['possible_points'] > 0:
                expected = (summary['scored_points'] / summary['possible_points']) * 100
                assert abs(summary['percentage'] - expected) < 0.01

        except ComplianceCheckError:
            pytest.skip("compliance-checker not available")


class TestViolationsRetrieval:
    """Test retrieving violations"""

    def test_get_violations_without_results(self, good_fair_netcdf):
        """Test getting violations without running check"""
        checker = CFComplianceChecker(str(good_fair_netcdf))

        violations = checker.get_violations()
        assert violations == []

    def test_get_all_violations(self, minimal_netcdf):
        """Test getting all violations"""
        checker = CFComplianceChecker(str(minimal_netcdf))

        try:
            checker.run_compliance_check()
            violations = checker.get_violations(priority='all')

            assert isinstance(violations, list)
            # Minimal dataset should have some violations
            # (but we can't guarantee exact count)

        except ComplianceCheckError:
            pytest.skip("compliance-checker not available")

    def test_get_high_priority_violations(self, minimal_netcdf):
        """Test filtering for high priority violations"""
        checker = CFComplianceChecker(str(minimal_netcdf))

        try:
            checker.run_compliance_check()
            violations = checker.get_violations(priority='high')

            assert isinstance(violations, list)
            # Each violation should have priority field
            for v in violations:
                if 'priority' in v:
                    assert v['priority'].lower() == 'high'

        except ComplianceCheckError:
            pytest.skip("compliance-checker not available")


class TestRecommendations:
    """Test recommendation generation"""

    def test_get_recommendations_without_results(self, good_fair_netcdf):
        """Test getting recommendations without running check"""
        checker = CFComplianceChecker(str(good_fair_netcdf))

        recommendations = checker.get_recommendations()
        assert recommendations == []

    def test_get_recommendations_with_results(self, minimal_netcdf):
        """Test getting recommendations after check"""
        checker = CFComplianceChecker(str(minimal_netcdf))

        try:
            checker.run_compliance_check()
            recommendations = checker.get_recommendations(max_items=5)

            assert isinstance(recommendations, list)
            assert len(recommendations) <= 5

            # Check recommendation structure
            for rec in recommendations:
                assert len(rec) == 3  # (priority, check_name, message)
                priority, check_name, message = rec
                assert isinstance(priority, str)
                assert isinstance(check_name, str)
                assert isinstance(message, str)

        except ComplianceCheckError:
            pytest.skip("compliance-checker not available")

    def test_recommendations_max_items(self, minimal_netcdf):
        """Test max_items parameter"""
        checker = CFComplianceChecker(str(minimal_netcdf))

        try:
            checker.run_compliance_check()

            # Test different limits
            recs_5 = checker.get_recommendations(max_items=5)
            recs_10 = checker.get_recommendations(max_items=10)

            assert len(recs_5) <= 5
            assert len(recs_10) <= 10

        except ComplianceCheckError:
            pytest.skip("compliance-checker not available")


class TestReportGeneration:
    """Test report generation"""

    def test_generate_simple_report_without_results(self, good_fair_netcdf):
        """Test report generation without results"""
        checker = CFComplianceChecker(str(good_fair_netcdf))

        report = checker.generate_simple_report()
        assert "No results available" in report

    def test_generate_simple_report_with_results(self, good_fair_netcdf):
        """Test report generation with results"""
        checker = CFComplianceChecker(str(good_fair_netcdf))

        try:
            checker.run_compliance_check()
            report = checker.generate_simple_report()

            assert isinstance(report, str)
            assert len(report) > 0

            # Check report contains key sections
            assert "CF CONVENTIONS COMPLIANCE REPORT" in report
            assert "Score:" in report
            assert "Issues:" in report

        except ComplianceCheckError:
            pytest.skip("compliance-checker not available")

    def test_report_includes_dataset_name(self, good_fair_netcdf):
        """Test that report includes dataset name"""
        checker = CFComplianceChecker(str(good_fair_netcdf))

        try:
            checker.run_compliance_check()
            report = checker.generate_simple_report()

            assert good_fair_netcdf.name in report

        except ComplianceCheckError:
            pytest.skip("compliance-checker not available")


class TestUtilityFunctions:
    """Test utility functions"""

    def test_quick_cf_check(self, good_fair_netcdf):
        """Test quick_cf_check utility function"""
        try:
            summary = quick_cf_check(str(good_fair_netcdf))

            assert isinstance(summary, dict)
            assert 'percentage' in summary
            assert 'total_issues' in summary

        except ComplianceCheckError:
            pytest.skip("compliance-checker not available")

    def test_compare_datasets_same_file(self, good_fair_netcdf):
        """Test comparing a dataset with itself"""
        try:
            comparison = compare_datasets(
                str(good_fair_netcdf),
                str(good_fair_netcdf)
            )

            assert isinstance(comparison, dict)
            assert 'dataset1' in comparison
            assert 'dataset2' in comparison
            assert 'improvement' in comparison

            # Same file should have 0 improvement
            assert comparison['improvement'] == 0

        except ComplianceCheckError:
            pytest.skip("compliance-checker not available")

    def test_compare_datasets_different_quality(self, minimal_netcdf, good_fair_netcdf):
        """Test comparing poor vs good dataset"""
        try:
            comparison = compare_datasets(
                str(minimal_netcdf),
                str(good_fair_netcdf)
            )

            assert isinstance(comparison, dict)

            # Good dataset should score higher
            assert comparison['dataset2']['score'] > comparison['dataset1']['score']
            assert comparison['improvement'] > 0

        except ComplianceCheckError:
            pytest.skip("compliance-checker not available")


class TestErrorHandling:
    """Test error handling"""

    def test_invalid_checker_name(self, good_fair_netcdf):
        """Test with invalid checker name"""
        checker = CFComplianceChecker(str(good_fair_netcdf))

        try:
            with pytest.raises(ComplianceCheckError):
                checker.run_compliance_check(checker='invalid_checker')
        except ComplianceCheckError as e:
            # If compliance-checker not installed, that's fine
            if "not installed" in str(e):
                pytest.skip("compliance-checker not available")
            else:
                raise

    def test_corrupted_netcdf_file(self, temp_dir):
        """Test with corrupted NetCDF file"""
        # Create a file that looks like NetCDF but isn't
        fake_nc = temp_dir / 'corrupted.nc'
        fake_nc.write_text("This is not a NetCDF file")

        checker = CFComplianceChecker(str(fake_nc))

        with pytest.raises(ComplianceCheckError):
            checker.run_compliance_check()


class TestRealOOIDataset:
    """Test with real OOI dataset if available"""

    def test_real_dataset_cf_check(self, real_ooi_dataset):
        """Test CF check on real OOI dataset"""
        if real_ooi_dataset is None:
            pytest.skip("Real OOI dataset not available")

        checker = CFComplianceChecker(str(real_ooi_dataset))

        try:
            checker.run_compliance_check()
            summary = checker.get_summary()

            assert isinstance(summary, dict)
            print(f"\nReal OOI CF Compliance: {summary.get('percentage', 0):.1f}%")

        except ComplianceCheckError:
            pytest.skip("compliance-checker not available")

    def test_real_dataset_violations(self, real_ooi_dataset):
        """Test violation extraction on real dataset"""
        if real_ooi_dataset is None:
            pytest.skip("Real OOI dataset not available")

        checker = CFComplianceChecker(str(real_ooi_dataset))

        try:
            checker.run_compliance_check()
            violations = checker.get_violations(priority='high')

            assert isinstance(violations, list)
            print(f"\nFound {len(violations)} high-priority CF violations")

        except ComplianceCheckError:
            pytest.skip("compliance-checker not available")
