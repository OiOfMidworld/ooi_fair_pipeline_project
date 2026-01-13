"""
FAIR Enrichment Pipeline

Orchestrates all enrichers to improve dataset FAIR compliance.
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional
import xarray as xr
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import get_logger
from transform.base_enricher import BaseEnricher
from transform.coordinate_enricher import CoordinateEnricher
from transform.variable_enricher import VariableEnricher
from transform.metadata_enricher import MetadataEnricher


logger = get_logger(__name__)


class FAIREnrichmentPipeline:
    """
    Complete FAIR enrichment pipeline

    Orchestrates multiple enrichers to improve dataset FAIR compliance.
    """

    def __init__(self, input_path: str, output_path: Optional[str] = None):
        """
        Initialize enrichment pipeline

        Parameters:
        -----------
        input_path : str
            Path to input NetCDF file
        output_path : str, optional
            Path to save enriched file (default: <input>_enriched.nc)
        """
        self.input_path = Path(input_path)
        self.output_path = Path(output_path) if output_path else None

        if not self.output_path:
            # Default output path
            stem = self.input_path.stem
            suffix = self.input_path.suffix
            self.output_path = self.input_path.parent / f"{stem}_enriched{suffix}"

        self.dataset = None
        self.enrichers = []
        self.summary = {}

        logger.info(f"Initialized enrichment pipeline")
        logger.info(f"  Input:  {self.input_path}")
        logger.info(f"  Output: {self.output_path}")

    def load_dataset(self):
        """Load the input dataset"""
        logger.info("Loading dataset...")
        self.dataset = xr.open_dataset(self.input_path)
        logger.info(f"Loaded dataset: {len(self.dataset.data_vars)} variables, "
                   f"{len(self.dataset.attrs)} global attributes")

    def run(self, enrichers: Optional[List[str]] = None) -> xr.Dataset:
        """
        Run the enrichment pipeline

        Parameters:
        -----------
        enrichers : list of str, optional
            List of enricher names to run. If None, run all.
            Options: 'coordinate', 'variable', 'metadata'

        Returns:
        --------
        xarray.Dataset: Enriched dataset
        """
        logger.info("="*60)
        logger.info("Starting FAIR Enrichment Pipeline")
        logger.info("="*60)

        start_time = datetime.now()

        # Load dataset if not already loaded
        if self.dataset is None:
            self.load_dataset()

        # Determine which enrichers to run
        if enrichers is None:
            enrichers = ['coordinate', 'variable', 'metadata']

        # Run enrichers in order
        enricher_map = {
            'coordinate': CoordinateEnricher,
            'variable': VariableEnricher,
            'metadata': MetadataEnricher
        }

        for enricher_name in enrichers:
            if enricher_name not in enricher_map:
                logger.warning(f"Unknown enricher: {enricher_name}, skipping")
                continue

            self._run_enricher(enricher_map[enricher_name])

        # Calculate metrics
        elapsed = (datetime.now() - start_time).total_seconds()

        logger.info("="*60)
        logger.info("Enrichment Complete")
        logger.info(f"Time elapsed: {elapsed:.2f}s")
        logger.info(f"Total changes: {self._count_total_changes()}")
        logger.info("="*60)

        return self.dataset

    def _run_enricher(self, enricher_class):
        """Run a single enricher"""
        enricher_name = enricher_class.__name__

        logger.info(f"\nRunning {enricher_name}...")

        try:
            enricher = enricher_class(self.dataset)
            self.dataset = enricher.enrich()

            # Validate
            if enricher.validate():
                logger.info(f"✅ {enricher_name} completed successfully")
            else:
                logger.warning(f"⚠️  {enricher_name} validation warnings")

            # Store summary
            summary = enricher.get_summary()
            self.enrichers.append(enricher)
            self.summary[enricher_name] = summary

            logger.info(f"   Changes: {summary['changes_made']}")
            logger.info(f"   Issues:  {summary['issues_found']}")

        except Exception as e:
            logger.error(f"❌ {enricher_name} failed: {e}")
            logger.debug("Exception details:", exc_info=True)
            raise

    def _count_total_changes(self) -> int:
        """Count total changes made across all enrichers"""
        return sum(
            enricher.get_summary()['changes_made']
            for enricher in self.enrichers
        )

    def save(self, output_path: Optional[str] = None):
        """
        Save enriched dataset

        Parameters:
        -----------
        output_path : str, optional
            Override output path
        """
        if output_path:
            self.output_path = Path(output_path)

        logger.info(f"Saving enriched dataset to: {self.output_path}")

        # Ensure output directory exists
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save dataset
        self.dataset.to_netcdf(self.output_path)

        file_size = self.output_path.stat().st_size / (1024 * 1024)
        logger.info(f"✅ Saved successfully ({file_size:.2f} MB)")

        return str(self.output_path)

    def get_enrichment_summary(self) -> Dict:
        """
        Get detailed summary of enrichment process

        Returns:
        --------
        dict: Summary with all enricher details
        """
        return {
            'input_file': str(self.input_path),
            'output_file': str(self.output_path),
            'enrichers_run': len(self.enrichers),
            'total_changes': self._count_total_changes(),
            'enrichers': self.summary
        }

    def print_summary(self):
        """Print human-readable summary"""
        print("\n" + "="*60)
        print("ENRICHMENT SUMMARY")
        print("="*60)

        print(f"\nInput:  {self.input_path.name}")
        print(f"Output: {self.output_path.name}")

        print(f"\nEnrichers Run: {len(self.enrichers)}")
        print(f"Total Changes: {self._count_total_changes()}")

        for enricher_name, summary in self.summary.items():
            print(f"\n{enricher_name}:")
            print(f"  Changes Made: {summary['changes_made']}")
            print(f"  Issues Found: {summary['issues_found']}")

            # Show sample changes
            if summary['changes']:
                print("  Sample Changes:")
                for change in summary['changes'][:3]:
                    print(f"    • {change['details']}")

        print("\n" + "="*60)


def quick_enrich(input_path: str, output_path: Optional[str] = None) -> str:
    """
    Quick enrichment utility

    Parameters:
    -----------
    input_path : str
        Path to input NetCDF file
    output_path : str, optional
        Path to save enriched file

    Returns:
    --------
    str: Path to enriched file
    """
    pipeline = FAIREnrichmentPipeline(input_path, output_path)
    pipeline.run()
    output = pipeline.save()
    pipeline.print_summary()

    return output
