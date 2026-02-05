"""
Quality Control module for BGC-Argo data.

Provides anomaly detection for pH and other biogeochemical variables.
"""

from qc.ph_anomaly_detector import PHAnomalyDetector

__all__ = ['PHAnomalyDetector']
