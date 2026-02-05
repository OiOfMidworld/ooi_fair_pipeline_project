#!/usr/bin/env python3
"""
Train pH Anomaly Detector

Downloads historical BGC-Argo data with pH sensors and trains
an IsolationForest model for anomaly detection.

Usage:
    python scripts/train_ph_detector.py

    # With custom number of profiles:
    python scripts/train_ph_detector.py --profiles 50

    # Use existing downloaded data:
    python scripts/train_ph_detector.py --use-existing
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import numpy as np
import xarray as xr

from extract.bgc_argo_api import BGCArgoExtractor
from qc.ph_anomaly_detector import PHAnomalyDetector
from utils.logging_config import get_logger

logger = get_logger(__name__)

# Directory for training data
TRAINING_DATA_DIR = PROJECT_ROOT / "data" / "training"
MODEL_OUTPUT_DIR = PROJECT_ROOT / "src" / "qc" / "models"


def download_training_data(n_profiles: int = 50) -> list:
    """
    Download BGC-Argo profiles with pH sensors.

    Args:
        n_profiles: Target number of profiles to download

    Returns:
        List of paths to downloaded files
    """
    logger.info(f"Downloading {n_profiles} BGC-Argo profiles with pH sensors...")

    TRAINING_DATA_DIR.mkdir(parents=True, exist_ok=True)

    extractor = BGCArgoExtractor()

    # Known floats with pH sensors (from previous exploration)
    # These are BGC-Argo floats known to have PH_IN_SITU_TOTAL
    ph_floats = [
        "5904468",  # North Pacific
        "5904471",  # North Pacific
        "5904659",  # Atlantic
        "6901528",  # Southern Ocean
        "6902745",  # Mediterranean
        "5906027",  # Pacific
        "5906028",  # Pacific
        "6903026",  # Indian Ocean
        "6903027",  # Atlantic
        "5906439",  # Pacific
    ]

    downloaded = []
    profiles_per_float = max(1, n_profiles // len(ph_floats))

    for float_id in ph_floats:
        if len(downloaded) >= n_profiles:
            break

        logger.info(f"Downloading profiles from float {float_id}...")

        # Try multiple profile numbers
        for profile_num in range(1, profiles_per_float * 3 + 1):
            if len(downloaded) >= n_profiles:
                break

            profile_str = f"{profile_num:03d}"
            output_path = TRAINING_DATA_DIR / f"BD{float_id}_{profile_str}.nc"

            if output_path.exists():
                logger.info(f"Already have {output_path.name}")
                downloaded.append(output_path)
                continue

            try:
                result = extractor.download_profile(
                    float_id, profile_str, str(output_path)
                )
                if result:
                    downloaded.append(output_path)
                    logger.info(f"Downloaded {output_path.name}")
            except Exception as e:
                logger.debug(f"Failed to download {float_id}_{profile_str}: {e}")
                continue

    logger.info(f"Downloaded {len(downloaded)} profiles")
    return downloaded


def load_existing_data() -> list:
    """Load already-downloaded training data."""
    if not TRAINING_DATA_DIR.exists():
        return []

    files = list(TRAINING_DATA_DIR.glob("*.nc"))
    logger.info(f"Found {len(files)} existing training files")
    return files


def extract_features(file_paths: list) -> tuple:
    """
    Extract pH, pressure, and temperature from NetCDF files.

    Returns:
        Tuple of (ph_array, pressure_array, temperature_array)
    """
    logger.info(f"Extracting features from {len(file_paths)} files...")

    all_ph = []
    all_pres = []
    all_temp = []

    ph_vars = ['PH_IN_SITU_TOTAL_ADJUSTED', 'PH_IN_SITU_TOTAL']
    pres_vars = ['PRES_ADJUSTED', 'PRES']
    temp_vars = ['TEMP_ADJUSTED', 'TEMP', 'TEMP_DOXY_ADJUSTED', 'TEMP_DOXY']

    for path in file_paths:
        try:
            ds = xr.open_dataset(path)

            # Find pH variable
            ph_var = None
            for var in ph_vars:
                if var in ds.variables:
                    ph_var = var
                    break

            if ph_var is None:
                logger.debug(f"No pH variable in {path.name}, skipping")
                ds.close()
                continue

            # Find pressure and temperature
            pres_var = next((v for v in pres_vars if v in ds.variables), None)
            temp_var = next((v for v in temp_vars if v in ds.variables), None)

            if pres_var is None or temp_var is None:
                logger.debug(f"Missing PRES or TEMP in {path.name}, skipping")
                ds.close()
                continue

            # Extract data
            ph_data = ds[ph_var].values.flatten()
            pres_data = ds[pres_var].values.flatten()
            temp_data = ds[temp_var].values.flatten()

            # Ensure same length
            min_len = min(len(ph_data), len(pres_data), len(temp_data))
            all_ph.extend(ph_data[:min_len])
            all_pres.extend(pres_data[:min_len])
            all_temp.extend(temp_data[:min_len])

            ds.close()
            logger.debug(f"Extracted {min_len} points from {path.name}")

        except Exception as e:
            logger.warning(f"Error processing {path.name}: {e}")
            continue

    # Convert to numpy arrays
    ph = np.array(all_ph)
    pres = np.array(all_pres)
    temp = np.array(all_temp)

    # Remove invalid values
    valid_mask = (
        np.isfinite(ph) & np.isfinite(pres) & np.isfinite(temp) &
        (ph > 0) & (ph < 14) &  # Valid pH range
        (pres >= 0) &  # Valid pressure
        (temp > -5) & (temp < 40)  # Reasonable ocean temperature
    )

    ph = ph[valid_mask]
    pres = pres[valid_mask]
    temp = temp[valid_mask]

    logger.info(f"Extracted {len(ph)} valid data points")

    return ph, pres, temp


def train_model(ph: np.ndarray, pres: np.ndarray, temp: np.ndarray) -> PHAnomalyDetector:
    """Train the anomaly detection model."""
    logger.info("Training IsolationForest model...")

    detector = PHAnomalyDetector(contamination=0.05)
    detector.train(ph, pres, temp)

    # Print some stats
    stats = detector.get_stats(ph, pres, temp)
    logger.info(f"Training complete:")
    logger.info(f"  Total points: {stats['total_points']}")
    logger.info(f"  Anomalies: {stats['anomalies']} ({stats['anomaly_percentage']:.1f}%)")

    return detector


def save_model(detector: PHAnomalyDetector):
    """Save the trained model."""
    MODEL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    model_path = MODEL_OUTPUT_DIR / "ph_isolation_forest.joblib"

    detector.save_model(model_path)
    logger.info(f"Model saved to {model_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Train pH anomaly detector on BGC-Argo data'
    )
    parser.add_argument(
        '--profiles', type=int, default=30,
        help='Number of profiles to download (default: 30)'
    )
    parser.add_argument(
        '--use-existing', action='store_true',
        help='Use existing downloaded data instead of downloading'
    )
    parser.add_argument(
        '--contamination', type=float, default=0.05,
        help='Expected anomaly proportion (default: 0.05)'
    )

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("pH ANOMALY DETECTOR TRAINING")
    print("=" * 60 + "\n")

    # Get training data
    if args.use_existing:
        file_paths = load_existing_data()
        if not file_paths:
            print("No existing data found. Run without --use-existing to download.")
            return 1
    else:
        file_paths = download_training_data(args.profiles)

    if len(file_paths) < 3:
        print(f"Not enough data files ({len(file_paths)}). Need at least 3.")
        return 1

    # Extract features
    ph, pres, temp = extract_features(file_paths)

    if len(ph) < 100:
        print(f"Not enough valid data points ({len(ph)}). Need at least 100.")
        return 1

    # Train model
    detector = PHAnomalyDetector(contamination=args.contamination)
    detector.train(ph, pres, temp)

    # Get training stats
    stats = detector.get_stats(ph, pres, temp)

    print("\n" + "-" * 40)
    print("TRAINING RESULTS")
    print("-" * 40)
    print(f"Training data points: {stats['total_points']}")
    print(f"Anomalies detected:   {stats['anomalies']} ({stats['anomaly_percentage']:.1f}%)")
    print("-" * 40)

    # Save model
    save_model(detector)

    print("\nModel training complete!")
    print(f"Model saved to: {MODEL_OUTPUT_DIR / 'ph_isolation_forest.joblib'}")
    print("\nThe anomaly enricher will now use this model automatically.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
