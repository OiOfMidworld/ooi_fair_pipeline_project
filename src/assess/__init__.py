"""
FAIR Assessment Module

Assesses OOI datasets against FAIR principles
"""

from .fair_metrics import (
    MetricScore,
    FAIRScore,
    FINDABLE_METRICS,
    ACCESSIBLE_METRICS,
    INTEROPERABLE_METRICS,
    REUSABLE_METRICS,
    get_improvement_recommendations
)

__all__ = [
    'MetricScore',
    'FAIRScore',
    'FINDABLE_METRICS',
    'ACCESSIBLE_METRICS',
    'INTEROPERABLE_METRICS',
    'REUSABLE_METRICS',
    'get_improvement_recommendations'
]
