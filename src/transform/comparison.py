"""
Before/After Comparison Tool

Compares FAIR scores and metadata between original and enriched datasets.
"""

import sys
from pathlib import Path
from typing import Dict, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import get_logger
from assess.fair_assessor import FAIRAssessor

logger = get_logger(__name__)


def compare_datasets(original_path: str, enriched_path: str) -> Dict:
    """
    Compare FAIR scores between original and enriched datasets

    Parameters:
    -----------
    original_path : str
        Path to original dataset
    enriched_path : str
        Path to enriched dataset

    Returns:
    --------
    dict: Comparison results
    """
    logger.info("Comparing datasets...")

    # Assess original
    logger.info("Assessing original dataset...")
    original_assessor = FAIRAssessor(original_path)
    original_score = original_assessor.assess()

    # Assess enriched
    logger.info("Assessing enriched dataset...")
    enriched_assessor = FAIRAssessor(enriched_path)
    enriched_score = enriched_assessor.assess()

    # Calculate improvements
    comparison = {
        'original': {
            'path': original_path,
            'total_score': original_score.total_score,
            'grade': original_score.grade,
            'findable': original_score.findable_score,
            'accessible': original_score.accessible_score,
            'interoperable': original_score.interoperable_score,
            'reusable': original_score.reusable_score
        },
        'enriched': {
            'path': enriched_path,
            'total_score': enriched_score.total_score,
            'grade': enriched_score.grade,
            'findable': enriched_score.findable_score,
            'accessible': enriched_score.accessible_score,
            'interoperable': enriched_score.interoperable_score,
            'reusable': enriched_score.reusable_score
        },
        'improvements': {
            'total_score': enriched_score.total_score - original_score.total_score,
            'grade_change': f"{original_score.grade} → {enriched_score.grade}",
            'findable': enriched_score.findable_score - original_score.findable_score,
            'accessible': enriched_score.accessible_score - original_score.accessible_score,
            'interoperable': enriched_score.interoperable_score - original_score.interoperable_score,
            'reusable': enriched_score.reusable_score - original_score.reusable_score
        }
    }

    return comparison


def print_comparison(comparison: Dict):
    """
    Print formatted comparison report

    Parameters:
    -----------
    comparison : dict
        Comparison results from compare_datasets
    """
    orig = comparison['original']
    enr = comparison['enriched']
    imp = comparison['improvements']

    print("\n" + "="*70)
    print("FAIR SCORE COMPARISON")
    print("="*70)

    print(f"\nOriginal Dataset: {Path(orig['path']).name}")
    print(f"Enriched Dataset: {Path(enr['path']).name}")

    print("\n" + "-"*70)
    print("SCORES")
    print("-"*70)

    # Total score
    print(f"\nTotal Score:")
    print(f"  Original:  {orig['total_score']:.1f}/100 (Grade: {orig['grade']})")
    print(f"  Enriched:  {enr['total_score']:.1f}/100 (Grade: {enr['grade']})")
    print(f"  Change:    {imp['total_score']:+.1f} points ({imp['grade_change']})")

    # Breakdown
    print(f"\nBreakdown:")

    categories = [
        ('Findable', 'findable', 25),
        ('Accessible', 'accessible', 20),
        ('Interoperable', 'interoperable', 30),
        ('Reusable', 'reusable', 25)
    ]

    for name, key, max_score in categories:
        change = imp[key]
        symbol = "✅" if change >= 0 else "⬇️"

        print(f"  {name:15s} {orig[key]:5.1f} → {enr[key]:5.1f} "
              f"({change:+.1f})  {symbol}")

    # Summary
    print("\n" + "-"*70)
    print("SUMMARY")
    print("-"*70)

    if imp['total_score'] > 0:
        print(f"\n✅ Enrichment successful!")
        print(f"   Improved by {imp['total_score']:.1f} points")

        if enr['grade'] != orig['grade']:
            print(f"   Grade improved from {orig['grade']} to {enr['grade']}")
    elif imp['total_score'] == 0:
        print(f"\n➖ No change in FAIR score")
        print(f"   Dataset already had good compliance")
    else:
        print(f"\n⚠️  FAIR score decreased")
        print(f"   This should not happen - check enrichment process")

    print("\n" + "="*70 + "\n")


def quick_compare(original_path: str, enriched_path: str):
    """
    Quick comparison utility with formatted output

    Parameters:
    -----------
    original_path : str
        Path to original dataset
    enriched_path : str
        Path to enriched dataset
    """
    comparison = compare_datasets(original_path, enriched_path)
    print_comparison(comparison)
    return comparison
