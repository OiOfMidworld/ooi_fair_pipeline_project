"""
CF Compliance Checker Integration

Integrates with IOOS compliance-checker to provide detailed CF convention
compliance analysis for NetCDF datasets.
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple
import tempfile

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import get_logger, ComplianceCheckError

logger = get_logger(__name__)


class CFComplianceChecker:
    """
    Check CF (Climate and Forecast) Conventions compliance

    Uses the IOOS compliance-checker library to validate datasets
    against CF conventions.
    """

    def __init__(self, dataset_path: str):
        """
        Initialize checker

        Parameters:
        -----------
        dataset_path : str
            Path to NetCDF file to check
        """
        self.dataset_path = Path(dataset_path)
        self.results = None
        logger.info(f"Initializing CF checker for: {self.dataset_path.name}")

    def run_compliance_check(self, checker='cf', verbose=1) -> Dict:
        """
        Run compliance check using compliance-checker

        Parameters:
        -----------
        checker : str
            Checker to use ('cf', 'acdd', 'ioos')
        verbose : int
            Verbosity level (0-5)

        Returns:
        --------
        dict: Compliance check results
        """
        try:
            from compliance_checker.runner import ComplianceChecker, CheckSuite

            logger.info(f"Running {checker} compliance check...")
            logger.debug(f"Dataset: {self.dataset_path}")

            # Load all available checker suites
            CheckSuite.load_all_available_checkers()

            # Run the check
            return_value, errors = ComplianceChecker.run_checker(
                ds_loc=str(self.dataset_path),
                checker_names=[checker],
                verbose=verbose,
                criteria='normal',
                output_filename=None,
                output_format='json'
            )

            # Parse results
            if checker in return_value:
                self.results = return_value[checker]
                logger.info("Compliance check complete")
                return self.results
            else:
                logger.error(f"No results for checker: {checker}")
                raise ComplianceCheckError(f"No results returned for {checker}")

        except ImportError:
            logger.error("compliance-checker not installed")
            raise ComplianceCheckError(
                "compliance-checker library not installed. "
                "Install with: pip install compliance-checker"
            )
        except Exception as e:
            logger.error(f"Compliance check failed: {e}")
            raise ComplianceCheckError(f"CF compliance check failed: {e}")

    def get_summary(self) -> Dict:
        """
        Get summary of compliance check results

        Returns:
        --------
        dict: Summary with counts and scores
        """
        if not self.results:
            logger.warning("No results available. Run check first.")
            return {}

        # Extract scored points
        scored = self.results.get('scored_points', 0)
        possible = self.results.get('possible_points', 0)

        # Count issues by priority
        high_priority = sum(
            1 for check in self.results.get('all_priorities', [])
            if check.get('priority', '').lower() == 'high'
        )

        medium_priority = sum(
            1 for check in self.results.get('all_priorities', [])
            if check.get('priority', '').lower() == 'medium'
        )

        low_priority = sum(
            1 for check in self.results.get('all_priorities', [])
            if check.get('priority', '').lower() == 'low'
        )

        summary = {
            'scored_points': scored,
            'possible_points': possible,
            'percentage': (scored / possible * 100) if possible > 0 else 0,
            'high_priority_issues': high_priority,
            'medium_priority_issues': medium_priority,
            'low_priority_issues': low_priority,
            'total_issues': high_priority + medium_priority + low_priority
        }

        logger.debug(f"CF Compliance: {summary['percentage']:.1f}% "
                    f"({scored}/{possible} points)")

        return summary

    def get_violations(self, priority: str = 'all') -> List[Dict]:
        """
        Get list of violations

        Parameters:
        -----------
        priority : str
            Filter by priority ('high', 'medium', 'low', 'all')

        Returns:
        --------
        list: Violations matching the priority filter
        """
        if not self.results:
            logger.warning("No results available. Run check first.")
            return []

        all_checks = self.results.get('all_priorities', [])

        if priority == 'all':
            violations = [
                check for check in all_checks
                if check.get('value', (0, 0))[0] < check.get('value', (0, 0))[1]
            ]
        else:
            violations = [
                check for check in all_checks
                if (check.get('priority', '').lower() == priority.lower() and
                    check.get('value', (0, 0))[0] < check.get('value', (0, 0))[1])
            ]

        return violations

    def get_recommendations(self, max_items: int = 10) -> List[Tuple[str, str, str]]:
        """
        Get prioritized list of fix recommendations

        Parameters:
        -----------
        max_items : int
            Maximum number of recommendations

        Returns:
        --------
        list: (priority, check_name, message) tuples
        """
        if not self.results:
            return []

        recommendations = []

        # Get high priority violations first
        for priority in ['high', 'medium', 'low']:
            violations = self.get_violations(priority)

            for violation in violations:
                check_name = violation.get('name', 'Unknown')
                messages = violation.get('msgs', [])

                # Extract useful message
                if messages:
                    message = messages[0] if isinstance(messages, list) else str(messages)
                else:
                    message = "See CF conventions documentation"

                recommendations.append((priority, check_name, message))

                if len(recommendations) >= max_items:
                    return recommendations

        return recommendations

    def generate_simple_report(self) -> str:
        """
        Generate a simple text report

        Returns:
        --------
        str: Formatted report
        """
        if not self.results:
            return "No results available. Run check first."

        summary = self.get_summary()

        report = []
        report.append("="*60)
        report.append("CF CONVENTIONS COMPLIANCE REPORT")
        report.append("="*60)
        report.append(f"\nDataset: {self.dataset_path.name}")
        report.append(f"\nScore: {summary['scored_points']}/{summary['possible_points']} "
                     f"({summary['percentage']:.1f}%)")
        report.append(f"\nIssues:")
        report.append(f"  High Priority:   {summary['high_priority_issues']}")
        report.append(f"  Medium Priority: {summary['medium_priority_issues']}")
        report.append(f"  Low Priority:    {summary['low_priority_issues']}")
        report.append(f"  Total:           {summary['total_issues']}")

        # Add top recommendations
        recommendations = self.get_recommendations(max_items=5)
        if recommendations:
            report.append("\nTop Recommendations:")
            for i, (priority, check, message) in enumerate(recommendations, 1):
                report.append(f"  {i}. [{priority.upper()}] {check}")
                report.append(f"     {message[:80]}...")

        report.append("\n" + "="*60)

        return "\n".join(report)


def quick_cf_check(dataset_path: str) -> Dict:
    """
    Quick CF compliance check utility

    Parameters:
    -----------
    dataset_path : str
        Path to NetCDF file

    Returns:
    --------
    dict: Summary results
    """
    checker = CFComplianceChecker(dataset_path)
    checker.run_compliance_check(checker='cf')
    return checker.get_summary()


def compare_datasets(dataset1_path: str, dataset2_path: str) -> Dict:
    """
    Compare CF compliance between two datasets

    Useful for before/after enrichment comparison

    Parameters:
    -----------
    dataset1_path : str
        Path to first dataset (e.g., original)
    dataset2_path : str
        Path to second dataset (e.g., enriched)

    Returns:
    --------
    dict: Comparison results
    """
    logger.info("Comparing CF compliance between datasets")

    checker1 = CFComplianceChecker(dataset1_path)
    checker1.run_compliance_check()
    summary1 = checker1.get_summary()

    checker2 = CFComplianceChecker(dataset2_path)
    checker2.run_compliance_check()
    summary2 = checker2.get_summary()

    comparison = {
        'dataset1': {
            'path': dataset1_path,
            'score': summary1['percentage']
        },
        'dataset2': {
            'path': dataset2_path,
            'score': summary2['percentage']
        },
        'improvement': summary2['percentage'] - summary1['percentage'],
        'issues_fixed': summary1['total_issues'] - summary2['total_issues']
    }

    logger.info(f"Dataset 1 score: {summary1['percentage']:.1f}%")
    logger.info(f"Dataset 2 score: {summary2['percentage']:.1f}%")
    logger.info(f"Improvement: {comparison['improvement']:.1f}%")

    return comparison
