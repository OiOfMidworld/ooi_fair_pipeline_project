"""
pH Anomaly Detection using IsolationForest.

Detects anomalous pH measurements in BGC-Argo data by considering
pH values in context of pressure (depth) and temperature.
"""

from pathlib import Path
from typing import Optional, Tuple
import numpy as np

try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    import joblib
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from utils.logging_config import get_logger

logger = get_logger(__name__)

# Default model path
DEFAULT_MODEL_PATH = Path(__file__).parent / "models" / "ph_isolation_forest.joblib"
DEFAULT_SCALER_PATH = Path(__file__).parent / "models" / "ph_scaler.joblib"


class PHAnomalyDetector:
    """
    Anomaly detector for BGC-Argo pH measurements.

    Uses IsolationForest to detect unusual pH values considering
    the oceanographic context (depth, temperature).

    Features used:
        - pH value
        - Pressure (proxy for depth)
        - Temperature

    Returns:
        -1 for anomalies, 1 for normal values
    """

    def __init__(
        self,
        model_path: Optional[Path] = None,
        scaler_path: Optional[Path] = None,
        contamination: float = 0.05,
    ):
        """
        Initialize the detector.

        Args:
            model_path: Path to saved IsolationForest model
            scaler_path: Path to saved StandardScaler
            contamination: Expected proportion of anomalies (default 5%)
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError(
                "scikit-learn is required for anomaly detection. "
                "Install with: pip install scikit-learn"
            )

        self.model_path = Path(model_path) if model_path else DEFAULT_MODEL_PATH
        self.scaler_path = Path(scaler_path) if scaler_path else DEFAULT_SCALER_PATH
        self.contamination = contamination

        self.model: Optional[IsolationForest] = None
        self.scaler: Optional[StandardScaler] = None
        self._is_trained = False

    def _prepare_features(
        self,
        ph: np.ndarray,
        pressure: np.ndarray,
        temperature: np.ndarray,
    ) -> np.ndarray:
        """
        Prepare feature matrix from input arrays.

        Handles NaN values by creating a mask and flattening arrays.

        Returns:
            Feature matrix of shape (n_samples, 3)
        """
        # Flatten arrays
        ph_flat = np.asarray(ph).flatten()
        pres_flat = np.asarray(pressure).flatten()
        temp_flat = np.asarray(temperature).flatten()

        # Stack features
        features = np.column_stack([ph_flat, pres_flat, temp_flat])

        return features

    def _get_valid_mask(self, features: np.ndarray) -> np.ndarray:
        """Return boolean mask of rows without NaN values."""
        return ~np.isnan(features).any(axis=1)

    def train(
        self,
        ph: np.ndarray,
        pressure: np.ndarray,
        temperature: np.ndarray,
        random_state: int = 42,
    ) -> "PHAnomalyDetector":
        """
        Train the anomaly detector on historical data.

        Args:
            ph: pH values (any shape, will be flattened)
            pressure: Pressure values in decibar
            temperature: Temperature values in Celsius
            random_state: Random seed for reproducibility

        Returns:
            self for method chaining
        """
        logger.info("Training pH anomaly detector...")

        # Prepare features
        features = self._prepare_features(ph, pressure, temperature)
        valid_mask = self._get_valid_mask(features)
        valid_features = features[valid_mask]

        if len(valid_features) < 10:
            raise ValueError(
                f"Insufficient valid data points for training: {len(valid_features)}. "
                "Need at least 10 non-NaN samples."
            )

        logger.info(f"Training on {len(valid_features)} valid samples")

        # Scale features
        self.scaler = StandardScaler()
        scaled_features = self.scaler.fit_transform(valid_features)

        # Train IsolationForest
        self.model = IsolationForest(
            contamination=self.contamination,
            random_state=random_state,
            n_estimators=100,
            max_samples='auto',
            n_jobs=-1,
        )
        self.model.fit(scaled_features)

        self._is_trained = True
        logger.info("Training complete")

        return self

    def detect(
        self,
        ph: np.ndarray,
        pressure: np.ndarray,
        temperature: np.ndarray,
    ) -> np.ndarray:
        """
        Detect anomalies in pH data.

        Args:
            ph: pH values
            pressure: Pressure values in decibar
            temperature: Temperature values in Celsius

        Returns:
            Array of same shape as input with -1 for anomalies, 1 for normal
        """
        if not self._is_trained:
            raise RuntimeError(
                "Detector not trained. Call train() or load_model() first."
            )

        original_shape = np.asarray(ph).shape
        features = self._prepare_features(ph, pressure, temperature)
        valid_mask = self._get_valid_mask(features)

        # Initialize results (default to normal)
        results = np.ones(len(features), dtype=np.int8)

        if valid_mask.sum() > 0:
            valid_features = features[valid_mask]
            scaled_features = self.scaler.transform(valid_features)
            predictions = self.model.predict(scaled_features)
            results[valid_mask] = predictions

        # Reshape to original
        return results.reshape(original_shape)

    def get_anomaly_scores(
        self,
        ph: np.ndarray,
        pressure: np.ndarray,
        temperature: np.ndarray,
    ) -> np.ndarray:
        """
        Get anomaly scores (lower = more anomalous).

        Returns:
            Array of anomaly scores, same shape as input
        """
        if not self._is_trained:
            raise RuntimeError(
                "Detector not trained. Call train() or load_model() first."
            )

        original_shape = np.asarray(ph).shape
        features = self._prepare_features(ph, pressure, temperature)
        valid_mask = self._get_valid_mask(features)

        # Initialize scores (default to 0 for NaN values)
        scores = np.zeros(len(features), dtype=np.float32)

        if valid_mask.sum() > 0:
            valid_features = features[valid_mask]
            scaled_features = self.scaler.transform(valid_features)
            scores[valid_mask] = self.model.decision_function(scaled_features)

        return scores.reshape(original_shape)

    def save_model(self, model_path: Optional[Path] = None) -> None:
        """Save the trained model and scaler to disk."""
        if not self._is_trained:
            raise RuntimeError("No trained model to save")

        model_path = Path(model_path) if model_path else self.model_path
        scaler_path = model_path.parent / f"{model_path.stem}_scaler.joblib"

        # Ensure directory exists
        model_path.parent.mkdir(parents=True, exist_ok=True)

        joblib.dump(self.model, model_path)
        joblib.dump(self.scaler, scaler_path)

        logger.info(f"Model saved to {model_path}")
        logger.info(f"Scaler saved to {scaler_path}")

    def load_model(self, model_path: Optional[Path] = None) -> "PHAnomalyDetector":
        """
        Load a pre-trained model from disk.

        Returns:
            self for method chaining
        """
        model_path = Path(model_path) if model_path else self.model_path
        scaler_path = model_path.parent / f"{model_path.stem}_scaler.joblib"

        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")
        if not scaler_path.exists():
            raise FileNotFoundError(f"Scaler not found: {scaler_path}")

        self.model = joblib.load(model_path)
        self.scaler = joblib.load(scaler_path)
        self._is_trained = True

        logger.info(f"Model loaded from {model_path}")

        return self

    @property
    def is_trained(self) -> bool:
        """Check if the detector has a trained model."""
        return self._is_trained

    def get_stats(
        self,
        ph: np.ndarray,
        pressure: np.ndarray,
        temperature: np.ndarray,
    ) -> dict:
        """
        Get detection statistics for a dataset.

        Returns:
            Dict with counts and percentages
        """
        predictions = self.detect(ph, pressure, temperature)
        flat = predictions.flatten()

        n_total = len(flat)
        n_anomalies = (flat == -1).sum()
        n_normal = (flat == 1).sum()

        return {
            "total_points": n_total,
            "anomalies": int(n_anomalies),
            "normal": int(n_normal),
            "anomaly_percentage": round(100 * n_anomalies / n_total, 2) if n_total > 0 else 0,
        }
