"""
FAIR Metrics and Scoring Rubric for OOI Datasets

This module defines the scoring criteria for evaluating datasets against
FAIR principles (Findable, Accessible, Interoperable, Reusable).

Based on:
- CF Conventions 1.6+
- ACDD (Attribute Convention for Data Discovery)
- OOI Data Portal requirements
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass, field


@dataclass
class MetricScore:
    """Individual metric score with details"""
    name: str
    points_earned: float
    points_possible: float
    status: str  # 'pass', 'fail', 'partial', 'warning'
    details: str = ""
    issues: List[str] = field(default_factory=list)

    @property
    def percentage(self) -> float:
        """Calculate percentage score"""
        if self.points_possible == 0:
            return 0.0
        return (self.points_earned / self.points_possible) * 100


@dataclass
class FAIRScore:
    """Complete FAIR assessment score"""
    findable_score: float
    accessible_score: float
    interoperable_score: float
    reusable_score: float
    total_score: float

    findable_details: List[MetricScore] = field(default_factory=list)
    accessible_details: List[MetricScore] = field(default_factory=list)
    interoperable_details: List[MetricScore] = field(default_factory=list)
    reusable_details: List[MetricScore] = field(default_factory=list)

    @property
    def grade(self) -> str:
        """Letter grade based on total score"""
        if self.total_score >= 90:
            return 'A'
        elif self.total_score >= 80:
            return 'B'
        elif self.total_score >= 70:
            return 'C'
        elif self.total_score >= 60:
            return 'D'
        else:
            return 'F'


# FAIR Scoring Rubric
# Total: 100 points distributed across 4 principles

# ============================================================================
# F - FINDABLE (25 points)
# ============================================================================

FINDABLE_METRICS = {
    'unique_identifier': {
        'points': 5,
        'description': 'Dataset has a unique, persistent identifier (DOI, UUID, etc.)',
        'required_attrs': ['id', 'uuid', 'doi', 'identifier'],
        'check_type': 'any'
    },
    'rich_metadata': {
        'points': 10,
        'description': 'Rich descriptive metadata about the data',
        'required_attrs': [
            'title', 'summary', 'keywords',
            'creator_name', 'institution', 'project'
        ],
        'check_type': 'all'
    },
    'searchable_metadata': {
        'points': 5,
        'description': 'Metadata includes searchable attributes',
        'required_attrs': [
            'geospatial_lat_min', 'geospatial_lat_max',
            'geospatial_lon_min', 'geospatial_lon_max',
            'time_coverage_start', 'time_coverage_end'
        ],
        'check_type': 'most'  # At least 4 of 6
    },
    'metadata_standard': {
        'points': 5,
        'description': 'Follows recognized metadata standards (ACDD, CF)',
        'required_attrs': ['Conventions', 'Metadata_Conventions'],
        'check_type': 'any'
    }
}

# ============================================================================
# A - ACCESSIBLE (20 points)
# ============================================================================

ACCESSIBLE_METRICS = {
    'access_protocol': {
        'points': 5,
        'description': 'Uses standard, open access protocol (HTTP, OPeNDAP)',
        'required_attrs': ['sourceUrl', 'datasetID'],
        'check_type': 'any'
    },
    'contact_info': {
        'points': 5,
        'description': 'Clear contact information for data access',
        'required_attrs': [
            'creator_email', 'publisher_email', 'contact'
        ],
        'check_type': 'any'
    },
    'access_constraints': {
        'points': 5,
        'description': 'Explicitly states access constraints or open access',
        'required_attrs': ['license', 'accessConstraints'],
        'check_type': 'any'
    },
    'authentication_metadata': {
        'points': 5,
        'description': 'Metadata accessible even if data requires authentication',
        'required_attrs': ['metadata_link', 'references'],
        'check_type': 'any'
    }
}

# ============================================================================
# I - INTEROPERABLE (30 points)
# ============================================================================

INTEROPERABLE_METRICS = {
    'cf_compliance': {
        'points': 15,
        'description': 'Complies with CF (Climate & Forecast) conventions',
        'required_checks': [
            'cf_conventions_version',
            'valid_variable_attributes',
            'coordinate_variables',
            'units_specified'
        ]
    },
    'standard_vocabulary': {
        'points': 5,
        'description': 'Uses standard vocabularies for variables',
        'required_attrs': ['standard_name', 'long_name'],
        'check_type': 'variables'
    },
    'data_format': {
        'points': 5,
        'description': 'Uses standard, open data format (NetCDF)',
        'formats': ['NetCDF', 'netCDF4', 'NETCDF4']
    },
    'coordinate_system': {
        'points': 5,
        'description': 'Clear coordinate system and projection info',
        'required_elements': ['lat', 'lon', 'time', 'depth']
    }
}

# ============================================================================
# R - REUSABLE (25 points)
# ============================================================================

REUSABLE_METRICS = {
    'clear_license': {
        'points': 5,
        'description': 'Clear usage license specified',
        'required_attrs': ['license'],
        'check_type': 'all'
    },
    'data_provenance': {
        'points': 8,
        'description': 'Clear data provenance and processing history',
        'required_attrs': [
            'source', 'processing_level', 'history',
            'creator_institution', 'date_created'
        ],
        'check_type': 'most'
    },
    'quality_control': {
        'points': 7,
        'description': 'Quality control flags and methodology documented',
        'required_elements': [
            'qc_variables', 'qc_flags', 'qartod_flags'
        ]
    },
    'community_standards': {
        'points': 5,
        'description': 'Follows domain-specific community standards',
        'required_attrs': [
            'Conventions', 'featureType', 'cdm_data_type'
        ],
        'check_type': 'most'
    }
}


# Helper functions for scoring calculations

def calculate_findable_score(metrics: List[MetricScore]) -> float:
    """Calculate total findable score"""
    earned = sum(m.points_earned for m in metrics)
    possible = sum(FINDABLE_METRICS[k]['points'] for k in FINDABLE_METRICS)
    return (earned / possible) * 25  # 25% of total


def calculate_accessible_score(metrics: List[MetricScore]) -> float:
    """Calculate total accessible score"""
    earned = sum(m.points_earned for m in metrics)
    possible = sum(ACCESSIBLE_METRICS[k]['points'] for k in ACCESSIBLE_METRICS)
    return (earned / possible) * 20  # 20% of total


def calculate_interoperable_score(metrics: List[MetricScore]) -> float:
    """Calculate total interoperable score"""
    earned = sum(m.points_earned for m in metrics)
    possible = sum(INTEROPERABLE_METRICS[k]['points'] for k in INTEROPERABLE_METRICS)
    return (earned / possible) * 30  # 30% of total


def calculate_reusable_score(metrics: List[MetricScore]) -> float:
    """Calculate total reusable score"""
    earned = sum(m.points_earned for m in metrics)
    possible = sum(REUSABLE_METRICS[k]['points'] for k in REUSABLE_METRICS)
    return (earned / possible) * 25  # 25% of total


# Priority fixes based on common issues

PRIORITY_FIXES = {
    'critical': [
        'Add unique persistent identifier (DOI or UUID)',
        'Add CF Conventions version to global attributes',
        'Add coordinate variables (lat, lon, time)',
        'Specify units for all variables',
        'Add clear data license'
    ],
    'high': [
        'Add geospatial bounding box metadata',
        'Add time coverage metadata',
        'Include creator and contact information',
        'Document data provenance',
        'Add standard_name attributes to variables'
    ],
    'medium': [
        'Improve variable descriptions (long_name)',
        'Document quality control procedures',
        'Add processing history',
        'Include references to related datasets',
        'Add keywords for discoverability'
    ],
    'low': [
        'Add contributor information',
        'Include acknowledgements',
        'Add more detailed comments',
        'Link to data access portal',
        'Add instrument metadata'
    ]
}


def get_improvement_recommendations(score: FAIRScore) -> List[Tuple[str, str, List[str]]]:
    """
    Get prioritized list of improvements

    Returns:
        List of (priority, category, recommendations)
    """
    recommendations = []

    # Analyze scores to determine what needs work
    if score.findable_score < 20:  # Less than 80% of findable
        recommendations.append(('critical', 'Findability', [
            'Add unique persistent identifier',
            'Improve descriptive metadata',
            'Add search-enabling metadata (geo bounds, time coverage)'
        ]))

    if score.accessible_score < 16:  # Less than 80% of accessible
        recommendations.append(('high', 'Accessibility', [
            'Add contact information',
            'Specify data access constraints/license',
            'Provide access protocol information'
        ]))

    if score.interoperable_score < 24:  # Less than 80% of interoperable
        recommendations.append(('critical', 'Interoperability', [
            'Achieve CF compliance',
            'Use standard variable names',
            'Define coordinate systems clearly'
        ]))

    if score.reusable_score < 20:  # Less than 80% of reusable
        recommendations.append(('high', 'Reusability', [
            'Add clear data license',
            'Document data provenance',
            'Include quality control information'
        ]))

    return recommendations
