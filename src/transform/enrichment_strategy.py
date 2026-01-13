"""
FAIR Enrichment Strategy

Defines the strategy for improving FAIR compliance based on assessment results.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum


class EnrichmentPriority(Enum):
    """Priority levels for enrichment tasks"""
    CRITICAL = 1  # Blocks CF compliance
    HIGH = 2      # Improves interoperability significantly
    MEDIUM = 3    # Improves discoverability
    LOW = 4       # Nice to have


@dataclass
class EnrichmentTask:
    """Represents a single enrichment task"""
    name: str
    description: str
    priority: EnrichmentPriority
    target_score_gain: float  # Expected score improvement
    affects_metrics: List[str]  # Which FAIR metrics this improves


# Enrichment Strategy based on Sprint 2 findings
ENRICHMENT_STRATEGY = {
    'coordinate_variables': EnrichmentTask(
        name='add_coordinate_variables',
        description='Add missing lat/lon coordinate variables',
        priority=EnrichmentPriority.CRITICAL,
        target_score_gain=2.5,
        affects_metrics=['coordinate_system', 'cf_compliance']
    ),
    'variable_units': EnrichmentTask(
        name='add_variable_units',
        description='Add units attribute to all variables',
        priority=EnrichmentPriority.CRITICAL,
        target_score_gain=4.0,
        affects_metrics=['cf_compliance', 'standard_vocabulary']
    ),
    'standard_names': EnrichmentTask(
        name='add_standard_names',
        description='Add CF standard_name to variables',
        priority=EnrichmentPriority.HIGH,
        target_score_gain=3.0,
        affects_metrics=['cf_compliance', 'standard_vocabulary']
    ),
    'global_metadata': EnrichmentTask(
        name='enhance_global_metadata',
        description='Add missing global attributes (DOI, creator_institution)',
        priority=EnrichmentPriority.MEDIUM,
        target_score_gain=1.0,
        affects_metrics=['findable', 'reusable']
    ),
    'qc_documentation': EnrichmentTask(
        name='document_qc_methodology',
        description='Add QC methodology documentation',
        priority=EnrichmentPriority.MEDIUM,
        target_score_gain=3.0,
        affects_metrics=['quality_control', 'reusable']
    ),
    'variable_metadata': EnrichmentTask(
        name='enhance_variable_metadata',
        description='Add long_name, valid_min/max, etc.',
        priority=EnrichmentPriority.LOW,
        target_score_gain=0.5,
        affects_metrics=['standard_vocabulary']
    )
}


def get_enrichment_plan(assessment_score: Dict) -> List[EnrichmentTask]:
    """
    Generate enrichment plan based on assessment results

    Parameters:
    -----------
    assessment_score : dict
        FAIR assessment results

    Returns:
    --------
    list of EnrichmentTask, prioritized
    """
    tasks = []

    # Get current scores
    interoperable_score = assessment_score.get('interoperable', 0)
    reusable_score = assessment_score.get('reusable', 0)

    # Critical: CF compliance issues
    if interoperable_score < 24:  # Less than 80% of 30 points
        tasks.append(ENRICHMENT_STRATEGY['coordinate_variables'])
        tasks.append(ENRICHMENT_STRATEGY['variable_units'])
        tasks.append(ENRICHMENT_STRATEGY['standard_names'])

    # High: Reusability improvements
    if reusable_score < 20:  # Less than 80% of 25 points
        tasks.append(ENRICHMENT_STRATEGY['qc_documentation'])
        tasks.append(ENRICHMENT_STRATEGY['global_metadata'])

    # Medium: Nice to have
    tasks.append(ENRICHMENT_STRATEGY['variable_metadata'])

    # Sort by priority
    tasks.sort(key=lambda t: t.priority.value)

    return tasks


# CF Standard Names mapping for common OOI variables
CF_STANDARD_NAMES = {
    # Temperature
    'temperature': 'sea_water_temperature',
    'temp': 'sea_water_temperature',
    'sea_water_temperature': 'sea_water_temperature',
    'seawater_temperature': 'sea_water_temperature',

    # Salinity
    'salinity': 'sea_water_practical_salinity',
    'sal': 'sea_water_practical_salinity',
    'sea_water_salinity': 'sea_water_practical_salinity',
    'sea_water_practical_salinity': 'sea_water_practical_salinity',

    # Pressure
    'pressure': 'sea_water_pressure',
    'pres': 'sea_water_pressure',
    'sea_water_pressure': 'sea_water_pressure',

    # Conductivity
    'conductivity': 'sea_water_electrical_conductivity',
    'cond': 'sea_water_electrical_conductivity',
    'sea_water_electrical_conductivity': 'sea_water_electrical_conductivity',

    # Dissolved Oxygen
    'oxygen': 'mole_concentration_of_dissolved_molecular_oxygen_in_sea_water',
    'do': 'mole_concentration_of_dissolved_molecular_oxygen_in_sea_water',
    'dissolved_oxygen': 'mole_concentration_of_dissolved_molecular_oxygen_in_sea_water',

    # pH
    'ph': 'sea_water_ph_reported_on_total_scale',
    'sea_water_ph': 'sea_water_ph_reported_on_total_scale',

    # Coordinates
    'time': 'time',
    'lat': 'latitude',
    'latitude': 'latitude',
    'lon': 'longitude',
    'longitude': 'longitude',
    'depth': 'depth',
    'altitude': 'altitude'
}


# Default units for common variables
DEFAULT_UNITS = {
    'sea_water_temperature': 'degree_C',
    'sea_water_practical_salinity': '1',  # PSU is deprecated
    'sea_water_pressure': 'dbar',
    'sea_water_electrical_conductivity': 'S m-1',
    'mole_concentration_of_dissolved_molecular_oxygen_in_sea_water': 'umol kg-1',
    'sea_water_ph_reported_on_total_scale': '1',
    'time': 'seconds since 1900-01-01T00:00:00Z',
    'latitude': 'degrees_north',
    'longitude': 'degrees_east',
    'depth': 'm',
    'altitude': 'm'
}


# OOI-specific metadata defaults
OOI_METADATA_DEFAULTS = {
    'institution': 'Ocean Observatories Initiative',
    'source': 'OOI Coastal Endurance Array',
    'project': 'Ocean Observatories Initiative',
    'publisher_name': 'Ocean Observatories Initiative',
    'publisher_url': 'https://oceanobservatories.org/',
    'license': 'These data may be used and redistributed for free, but are not intended for legal use, since they may contain inaccuracies.',
    'Conventions': 'CF-1.6, ACDD-1.3',
    'Metadata_Conventions': 'CF-1.6, ACDD-1.3',
    'cdm_data_type': 'TimeSeries',
    'featureType': 'timeSeries',
    'standard_name_vocabulary': 'CF Standard Name Table v79',
    'creator_type': 'institution',
    'creator_institution': 'Ocean Observatories Initiative',
    'publisher_type': 'institution',
    'publisher_institution': 'Ocean Observatories Initiative',
    'program': 'Ocean Observatories Initiative',
    'contributor_name': 'NSF, OOI Consortium',
    'contributor_role': 'sponsor, operator',
    'acknowledgement': 'National Science Foundation',
}


def get_variable_standard_name(variable_name: str) -> Optional[str]:
    """
    Get CF standard name for a variable

    Parameters:
    -----------
    variable_name : str
        Variable name

    Returns:
    --------
    str or None: CF standard name if found
    """
    # Try exact match
    name_lower = variable_name.lower()
    if name_lower in CF_STANDARD_NAMES:
        return CF_STANDARD_NAMES[name_lower]

    # Try partial matches
    for key, standard_name in CF_STANDARD_NAMES.items():
        if key in name_lower or name_lower in key:
            return standard_name

    return None


def get_variable_units(standard_name: str, variable_name: str = None) -> Optional[str]:
    """
    Get default units for a variable

    Parameters:
    -----------
    standard_name : str
        CF standard name
    variable_name : str, optional
        Variable name (fallback)

    Returns:
    --------
    str or None: Units if found
    """
    if standard_name in DEFAULT_UNITS:
        return DEFAULT_UNITS[standard_name]

    # Fallback: try variable name
    if variable_name:
        standard = get_variable_standard_name(variable_name)
        if standard and standard in DEFAULT_UNITS:
            return DEFAULT_UNITS[standard]

    return None


def estimate_total_improvement(tasks: List[EnrichmentTask]) -> float:
    """
    Estimate total FAIR score improvement

    Parameters:
    -----------
    tasks : list of EnrichmentTask
        Enrichment tasks to execute

    Returns:
    --------
    float: Estimated total score improvement
    """
    return sum(task.target_score_gain for task in tasks)
