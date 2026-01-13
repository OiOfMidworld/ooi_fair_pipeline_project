"""
FAIR Assessment Engine

Analyzes NetCDF datasets and scores them against FAIR principles.
"""

import sys
from pathlib import Path
import xarray as xr
from typing import List, Dict, Optional
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import get_logger, FAIRAssessmentError
from assess.fair_metrics import (
    MetricScore,
    FAIRScore,
    FINDABLE_METRICS,
    ACCESSIBLE_METRICS,
    INTEROPERABLE_METRICS,
    REUSABLE_METRICS,
    calculate_findable_score,
    calculate_accessible_score,
    calculate_interoperable_score,
    calculate_reusable_score,
    get_improvement_recommendations
)

logger = get_logger(__name__)


class FAIRAssessor:
    """
    Assess datasets against FAIR principles

    Evaluates:
    - F: Findability (metadata richness, identifiers, searchability)
    - A: Accessibility (protocols, contact info, constraints)
    - I: Interoperability (CF compliance, standards, formats)
    - R: Reusability (license, provenance, QC, community standards)
    """

    def __init__(self, dataset_path: str):
        """
        Initialize assessor with a dataset

        Parameters:
        -----------
        dataset_path : str
            Path to NetCDF dataset file
        """
        self.dataset_path = Path(dataset_path)
        self.dataset = None
        self.global_attrs = {}
        self.variables = {}

        logger.info(f"Initializing FAIR assessment for: {self.dataset_path.name}")

    def load_dataset(self):
        """Load and parse the NetCDF dataset"""
        try:
            logger.debug(f"Loading dataset: {self.dataset_path}")
            self.dataset = xr.open_dataset(self.dataset_path)

            # Extract metadata
            self.global_attrs = dict(self.dataset.attrs)
            self.variables = {
                var: dict(self.dataset[var].attrs)
                for var in self.dataset.data_vars
            }

            logger.info(f"Dataset loaded: {len(self.variables)} variables, "
                       f"{len(self.global_attrs)} global attributes")

        except Exception as e:
            logger.error(f"Failed to load dataset: {e}")
            raise FAIRAssessmentError(f"Cannot load dataset: {e}")

    def assess_findable(self) -> List[MetricScore]:
        """
        Assess Findability (F) metrics

        Checks for:
        - Unique persistent identifiers
        - Rich descriptive metadata
        - Searchable attributes
        - Standard metadata conventions
        """
        logger.info("Assessing Findability metrics")
        scores = []

        for metric_name, metric_def in FINDABLE_METRICS.items():
            score = self._evaluate_attribute_metric(
                metric_name,
                metric_def,
                self.global_attrs
            )
            scores.append(score)
            logger.debug(f"  {metric_name}: {score.points_earned}/{score.points_possible}")

        return scores

    def assess_accessible(self) -> List[MetricScore]:
        """
        Assess Accessibility (A) metrics

        Checks for:
        - Access protocols
        - Contact information
        - Access constraints/licensing
        - Metadata availability
        """
        logger.info("Assessing Accessibility metrics")
        scores = []

        for metric_name, metric_def in ACCESSIBLE_METRICS.items():
            score = self._evaluate_attribute_metric(
                metric_name,
                metric_def,
                self.global_attrs
            )
            scores.append(score)
            logger.debug(f"  {metric_name}: {score.points_earned}/{score.points_possible}")

        return scores

    def assess_interoperable(self) -> List[MetricScore]:
        """
        Assess Interoperability (I) metrics

        Checks for:
        - CF compliance
        - Standard vocabularies
        - Data formats
        - Coordinate systems
        """
        logger.info("Assessing Interoperability metrics")
        scores = []

        # CF Compliance - handled separately
        cf_score = self._evaluate_cf_compliance()
        scores.append(cf_score)

        # Standard vocabulary usage
        vocab_metric = INTEROPERABLE_METRICS['standard_vocabulary']
        vocab_score = self._evaluate_variable_attribute('standard_vocabulary', vocab_metric)
        scores.append(vocab_score)

        # Data format
        format_score = self._evaluate_data_format()
        scores.append(format_score)

        # Coordinate system
        coord_score = self._evaluate_coordinate_system()
        scores.append(coord_score)

        for score in scores:
            logger.debug(f"  {score.name}: {score.points_earned}/{score.points_possible}")

        return scores

    def assess_reusable(self) -> List[MetricScore]:
        """
        Assess Reusability (R) metrics

        Checks for:
        - Clear licensing
        - Data provenance
        - Quality control
        - Community standards
        """
        logger.info("Assessing Reusability metrics")
        scores = []

        # License
        license_metric = REUSABLE_METRICS['clear_license']
        license_score = self._evaluate_attribute_metric(
            'clear_license',
            license_metric,
            self.global_attrs
        )
        scores.append(license_score)

        # Provenance
        prov_metric = REUSABLE_METRICS['data_provenance']
        prov_score = self._evaluate_attribute_metric(
            'data_provenance',
            prov_metric,
            self.global_attrs
        )
        scores.append(prov_score)

        # Quality Control
        qc_score = self._evaluate_quality_control()
        scores.append(qc_score)

        # Community Standards
        std_metric = REUSABLE_METRICS['community_standards']
        std_score = self._evaluate_attribute_metric(
            'community_standards',
            std_metric,
            self.global_attrs
        )
        scores.append(std_score)

        for score in scores:
            logger.debug(f"  {score.name}: {score.points_earned}/{score.points_possible}")

        return scores

    def _evaluate_attribute_metric(
        self,
        metric_name: str,
        metric_def: Dict,
        attributes: Dict
    ) -> MetricScore:
        """
        Evaluate a metric based on attribute presence

        Parameters:
        -----------
        metric_name : str
            Name of the metric
        metric_def : dict
            Metric definition with required_attrs and check_type
        attributes : dict
            Attributes to check

        Returns:
        --------
        MetricScore
        """
        required = metric_def['required_attrs']
        check_type = metric_def['check_type']
        points = metric_def['points']

        found = [attr for attr in required if attr in attributes]
        missing = [attr for attr in required if attr not in attributes]

        # Calculate score based on check type
        if check_type == 'any':
            # Pass if ANY required attribute is present
            if len(found) > 0:
                earned = points
                status = 'pass'
                details = f"Found: {', '.join(found)}"
            else:
                earned = 0
                status = 'fail'
                details = f"Missing: {', '.join(missing)}"

        elif check_type == 'all':
            # Pass only if ALL required attributes are present
            if len(missing) == 0:
                earned = points
                status = 'pass'
                details = "All required attributes present"
            else:
                earned = (len(found) / len(required)) * points
                status = 'partial' if len(found) > 0 else 'fail'
                details = f"Missing: {', '.join(missing)}"

        elif check_type == 'most':
            # Pass if at least 2/3 of attributes are present
            threshold = len(required) * 0.67
            if len(found) >= threshold:
                earned = points
                status = 'pass'
                details = f"Found {len(found)}/{len(required)} attributes"
            else:
                earned = (len(found) / len(required)) * points
                status = 'partial' if len(found) > 0 else 'fail'
                details = f"Missing: {', '.join(missing)}"

        elif check_type == 'variables':
            # Check variable attributes
            return self._evaluate_variable_attribute(metric_name, metric_def)

        else:
            earned = 0
            status = 'fail'
            details = f"Unknown check type: {check_type}"

        return MetricScore(
            name=metric_name,
            points_earned=earned,
            points_possible=points,
            status=status,
            details=details,
            issues=missing if missing else []
        )

    def _evaluate_variable_attribute(self, metric_name: str, metric_def: Dict) -> MetricScore:
        """Evaluate metrics based on variable attributes"""
        required_attrs = metric_def['required_attrs']
        points = metric_def['points']

        total_vars = len(self.variables)
        if total_vars == 0:
            return MetricScore(
                name=metric_name,
                points_earned=0,
                points_possible=points,
                status='fail',
                details="No variables found",
                issues=[]
            )

        # Count how many variables have the required attributes
        vars_with_attrs = 0
        issues = []

        for var_name, var_attrs in self.variables.items():
            has_any_required = any(attr in var_attrs for attr in required_attrs)
            if has_any_required:
                vars_with_attrs += 1
            else:
                issues.append(f"{var_name} missing standard attributes")

        # Score based on percentage of compliant variables
        percentage = vars_with_attrs / total_vars
        earned = percentage * points

        if percentage >= 0.9:
            status = 'pass'
        elif percentage >= 0.5:
            status = 'partial'
        else:
            status = 'fail'

        return MetricScore(
            name=metric_name,
            points_earned=earned,
            points_possible=points,
            status=status,
            details=f"{vars_with_attrs}/{total_vars} variables have standard attributes",
            issues=issues[:5]  # Limit to first 5 issues
        )

    def _evaluate_cf_compliance(self) -> MetricScore:
        """Evaluate CF Conventions compliance"""
        metric_def = INTEROPERABLE_METRICS['cf_compliance']
        points = metric_def['points']

        issues = []
        earned = 0

        # Check 1: CF Conventions specified (3 points)
        if 'Conventions' in self.global_attrs:
            conventions = self.global_attrs['Conventions']
            if 'CF' in conventions:
                earned += 3
            else:
                issues.append("Conventions attribute doesn't mention CF")
        else:
            issues.append("Missing Conventions attribute")

        # Check 2: Variables have units (4 points)
        vars_with_units = sum(
            1 for attrs in self.variables.values()
            if 'units' in attrs
        )
        if self.variables:
            unit_ratio = vars_with_units / len(self.variables)
            earned += unit_ratio * 4
            if unit_ratio < 1.0:
                missing_count = len(self.variables) - vars_with_units
                issues.append(f"{missing_count} variables missing units")

        # Check 3: Coordinate variables present (4 points)
        coord_vars = ['time', 'lat', 'latitude', 'lon', 'longitude', 'depth', 'altitude']
        found_coords = [v for v in self.dataset.variables if any(c in v.lower() for c in coord_vars)]

        if len(found_coords) >= 2:  # At least time and one spatial coord
            earned += 4
        elif len(found_coords) >= 1:
            earned += 2
            issues.append("Incomplete coordinate variables")
        else:
            issues.append("Missing coordinate variables")

        # Check 4: Valid standard_names (4 points)
        vars_with_std_name = sum(
            1 for attrs in self.variables.values()
            if 'standard_name' in attrs
        )
        if self.variables:
            std_ratio = vars_with_std_name / len(self.variables)
            earned += std_ratio * 4
            if std_ratio < 0.5:
                issues.append("Less than 50% of variables have standard_name")

        # Determine status
        if earned >= points * 0.9:
            status = 'pass'
        elif earned >= points * 0.5:
            status = 'partial'
        else:
            status = 'fail'

        return MetricScore(
            name='cf_compliance',
            points_earned=earned,
            points_possible=points,
            status=status,
            details=f"CF compliance: {(earned/points)*100:.1f}%",
            issues=issues
        )

    def _evaluate_data_format(self) -> MetricScore:
        """Evaluate data format standards"""
        metric_def = INTEROPERABLE_METRICS['data_format']
        points = metric_def['points']

        # Check if it's NetCDF (we already know it is if we loaded it)
        if self.dataset_path.suffix in ['.nc', '.nc4', '.netcdf']:
            earned = points
            status = 'pass'
            details = f"Standard NetCDF format ({self.dataset_path.suffix})"
            issues = []
        else:
            earned = 0
            status = 'fail'
            details = f"Non-standard format: {self.dataset_path.suffix}"
            issues = ["Use NetCDF format for better interoperability"]

        return MetricScore(
            name='data_format',
            points_earned=earned,
            points_possible=points,
            status=status,
            details=details,
            issues=issues
        )

    def _evaluate_coordinate_system(self) -> MetricScore:
        """Evaluate coordinate system definition"""
        metric_def = INTEROPERABLE_METRICS['coordinate_system']
        points = metric_def['points']

        required_coords = metric_def['required_elements']
        found_coords = []
        issues = []

        # Check for coordinate variables
        for coord in required_coords:
            # Look for coordinate in variable names or attributes
            found = False
            for var_name in self.dataset.variables:
                if coord in var_name.lower():
                    found_coords.append(coord)
                    found = True
                    break

            if not found:
                issues.append(f"Missing {coord} coordinate")

        # Score based on found coordinates
        earned = (len(found_coords) / len(required_coords)) * points

        if len(found_coords) == len(required_coords):
            status = 'pass'
        elif len(found_coords) >= 2:
            status = 'partial'
        else:
            status = 'fail'

        return MetricScore(
            name='coordinate_system',
            points_earned=earned,
            points_possible=points,
            status=status,
            details=f"Found {len(found_coords)}/{len(required_coords)} coordinates",
            issues=issues
        )

    def _evaluate_quality_control(self) -> MetricScore:
        """Evaluate quality control documentation"""
        metric_def = REUSABLE_METRICS['quality_control']
        points = metric_def['points']

        # Look for QC-related variables
        qc_vars = [v for v in self.variables if 'qc' in v.lower() or 'qartod' in v.lower()]
        has_qc_vars = len(qc_vars) > 0

        # Look for QC attributes
        qc_attrs = [a for a in self.global_attrs if 'quality' in a.lower() or 'qc' in a.lower()]
        has_qc_attrs = len(qc_attrs) > 0

        earned = 0
        issues = []

        if has_qc_vars:
            earned += 4
        else:
            issues.append("No QC flag variables found")

        if has_qc_attrs:
            earned += 3
        else:
            issues.append("No QC methodology documentation")

        if earned >= points * 0.8:
            status = 'pass'
        elif earned >= points * 0.4:
            status = 'partial'
        else:
            status = 'fail'

        return MetricScore(
            name='quality_control',
            points_earned=earned,
            points_possible=points,
            status=status,
            details=f"Found {len(qc_vars)} QC variables",
            issues=issues
        )

    def assess(self) -> FAIRScore:
        """
        Perform complete FAIR assessment

        Returns:
        --------
        FAIRScore with detailed results
        """
        logger.info("="*60)
        logger.info(f"Starting FAIR Assessment: {self.dataset_path.name}")
        logger.info("="*60)

        # Load dataset
        self.load_dataset()

        # Assess each principle
        findable_details = self.assess_findable()
        accessible_details = self.assess_accessible()
        interoperable_details = self.assess_interoperable()
        reusable_details = self.assess_reusable()

        # Calculate scores
        findable_score = calculate_findable_score(findable_details)
        accessible_score = calculate_accessible_score(accessible_details)
        interoperable_score = calculate_interoperable_score(interoperable_details)
        reusable_score = calculate_reusable_score(reusable_details)
        total_score = findable_score + accessible_score + interoperable_score + reusable_score

        score = FAIRScore(
            findable_score=findable_score,
            accessible_score=accessible_score,
            interoperable_score=interoperable_score,
            reusable_score=reusable_score,
            total_score=total_score,
            findable_details=findable_details,
            accessible_details=accessible_details,
            interoperable_details=interoperable_details,
            reusable_details=reusable_details
        )

        logger.info("Assessment complete")
        logger.info(f"Total FAIR Score: {total_score:.1f}/100 (Grade: {score.grade})")
        logger.info(f"  Findable:       {findable_score:.1f}/25")
        logger.info(f"  Accessible:     {accessible_score:.1f}/20")
        logger.info(f"  Interoperable:  {interoperable_score:.1f}/30")
        logger.info(f"  Reusable:       {reusable_score:.1f}/25")

        return score

    def generate_report(self, score: FAIRScore, output_path: Optional[str] = None) -> str:
        """
        Generate detailed assessment report

        Parameters:
        -----------
        score : FAIRScore
            Assessment results
        output_path : str, optional
            Path to save JSON report

        Returns:
        --------
        str: Path to saved report or JSON string
        """
        report = {
            'dataset': str(self.dataset_path),
            'timestamp': str(Path(self.dataset_path).stat().st_mtime),
            'summary': {
                'total_score': round(score.total_score, 2),
                'grade': score.grade,
                'findable': round(score.findable_score, 2),
                'accessible': round(score.accessible_score, 2),
                'interoperable': round(score.interoperable_score, 2),
                'reusable': round(score.reusable_score, 2)
            },
            'details': {
                'findable': [self._metric_to_dict(m) for m in score.findable_details],
                'accessible': [self._metric_to_dict(m) for m in score.accessible_details],
                'interoperable': [self._metric_to_dict(m) for m in score.interoperable_details],
                'reusable': [self._metric_to_dict(m) for m in score.reusable_details]
            },
            'recommendations': [
                {'priority': p, 'category': c, 'items': items}
                for p, c, items in get_improvement_recommendations(score)
            ]
        }

        if output_path:
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Report saved to: {output_path}")
            return output_path
        else:
            return json.dumps(report, indent=2)

    @staticmethod
    def _metric_to_dict(metric: MetricScore) -> Dict:
        """Convert MetricScore to dictionary"""
        return {
            'name': metric.name,
            'points_earned': round(metric.points_earned, 2),
            'points_possible': metric.points_possible,
            'percentage': round(metric.percentage, 1),
            'status': metric.status,
            'details': metric.details,
            'issues': metric.issues
        }
