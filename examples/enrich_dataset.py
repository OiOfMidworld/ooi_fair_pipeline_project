"""
FAIR Enrichment Demo Script

Demonstrates the complete enrichment workflow:
1. Load original dataset
2. Run enrichment pipeline
3. Compare before/after FAIR scores
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils import setup_logging
from transform.enrichment_pipeline import FAIREnrichmentPipeline
from transform.comparison import quick_compare

# Set up logging
logger = setup_logging(name='demo.enrich', level='INFO')


def enrich_and_compare(input_path: str):
    """
    Complete enrichment workflow with before/after comparison

    Parameters:
    -----------
    input_path : str
        Path to dataset to enrich
    """
    print("\n" + "="*70)
    print("  OOI FAIR ENRICHMENT DEMO")
    print("="*70 + "\n")

    input_file = Path(input_path)

    if not input_file.exists():
        print(f"❌ Dataset not found: {input_path}")
        print("\nPlease provide a valid NetCDF file path.")
        return

    print(f"Input Dataset: {input_file.name}\n")

    # ==================================================================
    # Part 1: Run Enrichment Pipeline
    # ==================================================================

    print("="*70)
    print("PART 1: RUNNING ENRICHMENT PIPELINE")
    print("="*70 + "\n")

    # Create pipeline
    pipeline = FAIREnrichmentPipeline(str(input_file))

    # Run enrichment
    enriched_dataset = pipeline.run()

    # Save enriched dataset
    output_path = pipeline.save()

    # Print summary
    pipeline.print_summary()

    # ==================================================================
    # Part 2: Compare FAIR Scores
    # ==================================================================

    print("\n" + "="*70)
    print("PART 2: BEFORE/AFTER COMPARISON")
    print("="*70 + "\n")

    quick_compare(str(input_file), output_path)

    # ==================================================================
    # Part 3: Detailed Change Log
    # ==================================================================

    print("="*70)
    print("PART 3: DETAILED CHANGES")
    print("="*70 + "\n")

    summary = pipeline.get_enrichment_summary()

    for enricher_name, enricher_summary in summary['enrichers'].items():
        print(f"\n{enricher_name}:")
        print(f"  Total Changes: {enricher_summary['changes_made']}")

        if enricher_summary['changes']:
            print("  Changes:")
            for change in enricher_summary['changes'][:10]:  # Show first 10
                print(f"    • [{change['type']}] {change['details']}")

        if enricher_summary['issues']:
            print("  Issues:")
            for issue in enricher_summary['issues'][:5]:  # Show first 5
                print(f"    ⚠️  [{issue['type']}] {issue['details']}")

    # ==================================================================
    # Summary
    # ==================================================================

    print("\n" + "="*70)
    print("ENRICHMENT COMPLETE")
    print("="*70 + "\n")

    print("Results:")
    print(f"  Original File:  {input_file}")
    print(f"  Enriched File:  {output_path}")
    print(f"  Total Changes:  {summary['total_changes']}")

    print("\nNext Steps:")
    print("  1. Review the enriched dataset")
    print("  2. Run FAIR assessment on enriched data")
    print("  3. Compare with original assessment")
    print("  4. Iterate on enrichment rules if needed")

    print("\n" + "="*70 + "\n")


def main():
    """Main entry point"""
    import sys

    if len(sys.argv) > 1:
        # Use provided dataset path
        input_path = sys.argv[1]
    else:
        # Default to sample dataset
        input_path = 'data/raw/test_download.nc'

    enrich_and_compare(input_path)


if __name__ == "__main__":
    main()
