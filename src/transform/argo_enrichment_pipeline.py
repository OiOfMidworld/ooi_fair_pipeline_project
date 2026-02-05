"""
BGC-Argo FAIR Enrichment Pipeline

Specialized pipeline for BGC-Argo float data enrichment.

Orchestrates Argo-specific enrichers to transform BGC-Argo data
from Grade F (49.2/100) to Grade A (90+/100) for mCDR/MRV applications.

Sprint: 4B - BGC-Argo mCDR/MRV Extension
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional
import xarray as xr
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import get_logger
from transform.argo_metadata_enricher import ArgoMetadataEnricher
from transform.geospatial_extractor import GeospatialExtractor
from transform.bgc_standard_name_mapper import BGCStandardNameMapper
from transform.metadata_enricher import MetadataEnricher  # Reuse existing
from transform.anomaly_enricher import AnomalyEnricher

logger = get_logger(__name__)


class ArgoEnrichmentPipeline:
    """
    Complete BGC-Argo enrichment pipeline

    Transforms raw BGC-Argo data into FAIR-compliant,
    verification-ready datasets for mCDR/MRV.
    """

    def __init__(self, input_path: str, output_path: Optional[str] = None):
        """
        Initialize Argo enrichment pipeline

        Parameters:
        -----------
        input_path : str
            Path to input NetCDF file (BGC-Argo profile)
        output_path : str, optional
            Path to save enriched file
        """
        self.input_path = Path(input_path)
        self.output_path = Path(output_path) if output_path else None

        if not self.output_path:
            # Default: add _enriched suffix
            stem = self.input_path.stem
            suffix = self.input_path.suffix
            self.output_path = self.input_path.parent / f"{stem}_enriched{suffix}"

        self.dataset = None
        self.enrichers = []
        self.summary = {}

        logger.info("Initialized BGC-Argo enrichment pipeline")
        logger.info(f"  Input:  {self.input_path}")
        logger.info(f"  Output: {self.output_path}")

    def load_dataset(self):
        """Load the input dataset"""
        logger.info("Loading BGC-Argo dataset...")
        self.dataset = xr.open_dataset(self.input_path)
        logger.info(f"Loaded dataset: {len(self.dataset.data_vars)} variables, "
                   f"{len(self.dataset.attrs)} global attributes")

    def run(self, enrichers: Optional[List[str]] = None) -> xr.Dataset:
        """
        Run the Argo enrichment pipeline

        Parameters:
        -----------
        enrichers : list of str, optional
            List of enricher names to run. If None, run all.
            Options: 'geospatial', 'argo_metadata', 'bgc_names', 'metadata'

        Returns:
        --------
        xarray.Dataset: Enriched dataset
        """
        logger.info("="*60)
        logger.info("Starting BGC-Argo FAIR Enrichment Pipeline")
        logger.info("="*60)

        start_time = datetime.now()

        # Load dataset if not already loaded
        if self.dataset is None:
            self.load_dataset()

        # Determine which enrichers to run
        if enrichers is None:
            enrichers = ['geospatial', 'argo_metadata', 'anomaly', 'bgc_names', 'metadata']

        # Run enrichers in order
        enricher_map = {
            'geospatial': lambda: GeospatialExtractor(self.dataset),
            'argo_metadata': lambda: ArgoMetadataEnricher(
                self.dataset,
                file_path=str(self.input_path)
            ),
            'anomaly': lambda: AnomalyEnricher(self.dataset),
            'bgc_names': lambda: BGCStandardNameMapper(self.dataset),
            'metadata': lambda: MetadataEnricher(self.dataset),
        }

        for enricher_name in enrichers:
            if enricher_name not in enricher_map:
                logger.warning(f"Unknown enricher: {enricher_name}, skipping")
                continue

            self._run_enricher(enricher_map[enricher_name]())

        # Calculate metrics
        elapsed = (datetime.now() - start_time).total_seconds()

        logger.info("="*60)
        logger.info("Enrichment Complete")
        logger.info(f"Time elapsed: {elapsed:.2f}s")
        logger.info(f"Total changes: {self._count_total_changes()}")
        logger.info("="*60)

        return self.dataset

    def _run_enricher(self, enricher):
        """Run a single enricher"""
        enricher_name = enricher.__class__.__name__

        logger.info(f"\nRunning {enricher_name}...")

        try:
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
        print("BGC-ARGO ENRICHMENT SUMMARY")
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
                for change in summary['changes'][:5]:
                    print(f"    • {change['details']}")

        print("\n" + "="*60)


def quick_enrich_argo(input_path: str, output_path: Optional[str] = None) -> str:
    """
    Quick enrichment utility for BGC-Argo data

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
    pipeline = ArgoEnrichmentPipeline(input_path, output_path)
    pipeline.run()
    output = pipeline.save()
    pipeline.print_summary()

    return output


def main():
    """Demo/test function"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Enrich BGC-Argo data for FAIR compliance'
    )
    parser.add_argument('input_file',
                       help='Input BGC-Argo NetCDF file')
    parser.add_argument('-o', '--output',
                       help='Output file path (optional)')

    args = parser.parse_args()

    print("\n" + "="*60)
    print("BGC-ARGO FAIR ENRICHMENT PIPELINE")
    print("="*60 + "\n")

    try:
        output = quick_enrich_argo(args.input_file, args.output)

        print("\n✅ Enrichment successful!")
        print(f"\nEnriched file: {output}")
        print("\nNext steps:")
        print("1. Run FAIR assessment:")
        print(f"   python3 examples/assess_dataset.py {output}")
        print("\n2. Compare with original:")
        print(f"   python3 examples/assess_dataset.py {args.input_file}")

    except Exception as e:
        print(f"\n❌ Enrichment failed: {e}")
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
