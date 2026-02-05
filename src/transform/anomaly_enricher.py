"""
Anomaly Detection Enricher

Adds AI-based quality flags to BGC-Argo data using IsolationForest
anomaly detection on pH measurements.
"""

from typing import Optional
import numpy as np
import xarray as xr

from transform.base_enricher import BaseEnricher

# Try to import detector, but allow graceful degradation
try:
    from qc.ph_anomaly_detector import PHAnomalyDetector
    DETECTOR_AVAILABLE = True
except ImportError:
    DETECTOR_AVAILABLE = False


class AnomalyEnricher(BaseEnricher):
    """
    Enricher that adds AI-based anomaly detection flags to pH data.

    Uses IsolationForest trained on historical BGC-Argo profiles to
    identify suspicious pH measurements. Adds CF-compliant quality
    flag variables to the output dataset.

    Requires:
        - PH_IN_SITU_TOTAL or PH_IN_SITU_TOTAL_ADJUSTED variable
        - PRES or PRES_ADJUSTED variable
        - TEMP or TEMP_ADJUSTED variable
    """

    # Variable name candidates (in order of preference)
    PH_VARS = ['PH_IN_SITU_TOTAL_ADJUSTED', 'PH_IN_SITU_TOTAL']
    PRES_VARS = ['PRES_ADJUSTED', 'PRES']
    TEMP_VARS = ['TEMP_ADJUSTED', 'TEMP', 'TEMP_DOXY_ADJUSTED', 'TEMP_DOXY']

    def __init__(
        self,
        dataset: xr.Dataset,
        detector: Optional["PHAnomalyDetector"] = None,
        skip_if_no_model: bool = True,
        logger=None,
    ):
        """
        Initialize the anomaly enricher.

        Args:
            dataset: xarray Dataset to enrich
            detector: Pre-configured PHAnomalyDetector (optional)
            skip_if_no_model: If True, skip enrichment if no model found
            logger: Logger instance
        """
        super().__init__(dataset, logger)
        self.detector = detector
        self.skip_if_no_model = skip_if_no_model

        # Track which variables we found
        self._ph_var = None
        self._pres_var = None
        self._temp_var = None

    def _find_variable(self, candidates: list) -> Optional[str]:
        """Find first matching variable name from candidates."""
        for name in candidates:
            if name in self.dataset.variables:
                return name
        return None

    def _load_detector(self) -> bool:
        """
        Load the anomaly detector model.

        Returns:
            True if detector is ready, False otherwise
        """
        if not DETECTOR_AVAILABLE:
            self.log_issue(
                'missing_dependency',
                'scikit-learn not installed, skipping anomaly detection'
            )
            return False

        if self.detector is None:
            self.detector = PHAnomalyDetector()
            try:
                self.detector.load_model()
            except FileNotFoundError as e:
                if self.skip_if_no_model:
                    self.log_issue(
                        'no_model',
                        f'Anomaly detection model not found: {e}. '
                        'Run training script first.'
                    )
                    return False
                else:
                    raise

        return self.detector.is_trained

    def _check_required_variables(self) -> bool:
        """
        Check that required variables exist in the dataset.

        Returns:
            True if all required variables found
        """
        self._ph_var = self._find_variable(self.PH_VARS)
        self._pres_var = self._find_variable(self.PRES_VARS)
        self._temp_var = self._find_variable(self.TEMP_VARS)

        missing = []
        if self._ph_var is None:
            missing.append('pH (PH_IN_SITU_TOTAL)')
        if self._pres_var is None:
            missing.append('Pressure (PRES)')
        if self._temp_var is None:
            missing.append('Temperature (TEMP)')

        if missing:
            self.log_issue(
                'missing_variables',
                f"Required variables not found: {', '.join(missing)}. "
                "Skipping anomaly detection."
            )
            return False

        self.logger.info(
            f"Found variables: pH={self._ph_var}, "
            f"PRES={self._pres_var}, TEMP={self._temp_var}"
        )
        return True

    def enrich(self) -> xr.Dataset:
        """
        Apply anomaly detection to pH data.

        Adds PH_ANOMALY_FLAG variable with CF-compliant attributes.

        Returns:
            Enriched dataset with anomaly flags
        """
        self.logger.info("Starting anomaly detection enrichment")
        ds = self.dataset.copy(deep=True)

        # Check prerequisites
        if not self._check_required_variables():
            self.dataset = ds
            return ds

        if not self._load_detector():
            self.dataset = ds
            return ds

        # Get data arrays
        ph_data = ds[self._ph_var].values
        pres_data = ds[self._pres_var].values
        temp_data = ds[self._temp_var].values

        # Run anomaly detection
        self.logger.info("Running IsolationForest anomaly detection...")
        try:
            anomaly_flags = self.detector.detect(ph_data, pres_data, temp_data)
            anomaly_scores = self.detector.get_anomaly_scores(ph_data, pres_data, temp_data)
            stats = self.detector.get_stats(ph_data, pres_data, temp_data)
        except Exception as e:
            self.log_issue('detection_error', f"Anomaly detection failed: {e}")
            self.dataset = ds
            return ds

        # Add anomaly flag variable
        ds['PH_ANOMALY_FLAG'] = xr.DataArray(
            anomaly_flags,
            dims=ds[self._ph_var].dims,
            attrs={
                'long_name': 'pH anomaly detection flag',
                'standard_name': 'quality_flag',
                'flag_values': np.array([-1, 1], dtype=np.int8),
                'flag_meanings': 'anomaly normal',
                'comment': (
                    'Anomaly detection using IsolationForest algorithm. '
                    'Trained on historical BGC-Argo pH profiles. '
                    '-1 indicates potential anomaly, 1 indicates normal.'
                ),
                'source_variable': self._ph_var,
            }
        )
        self.log_change(
            'variable_added',
            f"Added PH_ANOMALY_FLAG ({stats['anomalies']} anomalies detected)"
        )

        # Add anomaly score variable (continuous)
        ds['PH_ANOMALY_SCORE'] = xr.DataArray(
            anomaly_scores,
            dims=ds[self._ph_var].dims,
            attrs={
                'long_name': 'pH anomaly score',
                'comment': (
                    'IsolationForest anomaly score. '
                    'Lower values indicate more anomalous measurements.'
                ),
                'units': '1',
                'source_variable': self._ph_var,
            }
        )
        self.log_change('variable_added', 'Added PH_ANOMALY_SCORE')

        # Add global metadata
        ds.attrs['anomaly_detection_method'] = 'IsolationForest (scikit-learn)'
        ds.attrs['anomaly_detection_variables'] = 'PH_IN_SITU_TOTAL, PRES, TEMP'
        ds.attrs['anomaly_count'] = stats['anomalies']
        ds.attrs['anomaly_percentage'] = stats['anomaly_percentage']
        self.log_change(
            'attribute_added',
            f"Added anomaly detection metadata "
            f"({stats['anomaly_percentage']:.1f}% anomalies)"
        )

        self.logger.info(
            f"Anomaly detection complete: {stats['anomalies']}/{stats['total_points']} "
            f"points flagged ({stats['anomaly_percentage']:.1f}%)"
        )

        self.dataset = ds
        return ds

    def validate(self) -> bool:
        """
        Validate that anomaly detection was successful.

        Returns:
            True if validation passed
        """
        ds = self.dataset

        # Check if we have the expected outputs
        if 'PH_ANOMALY_FLAG' not in ds.variables:
            # May have been skipped due to missing model/variables
            if self.issues_found:
                self.logger.info(
                    "Anomaly detection skipped (see issues), validation passed"
                )
                return True
            self.logger.warning("PH_ANOMALY_FLAG variable not found")
            return False

        # Verify flag values are valid
        flag_var = ds['PH_ANOMALY_FLAG']
        unique_vals = np.unique(flag_var.values[~np.isnan(flag_var.values.astype(float))])

        if not all(v in [-1, 1] for v in unique_vals):
            self.logger.warning(f"Unexpected flag values: {unique_vals}")
            return False

        # Verify required attributes
        required_attrs = ['long_name', 'flag_values', 'flag_meanings']
        missing = [a for a in required_attrs if a not in flag_var.attrs]
        if missing:
            self.logger.warning(f"Missing attributes on PH_ANOMALY_FLAG: {missing}")
            return False

        self.logger.info("Anomaly enrichment validation passed")
        return True
