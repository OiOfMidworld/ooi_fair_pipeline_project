"""
FAIR Assessment Demo Script

Demonstrates how to use the FAIR assessment engine to score OOI datasets.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils import setup_logging
from assess.fair_assessor import FAIRAssessor
from assess.cf_checker import CFComplianceChecker, quick_cf_check
from assess.fair_metrics import get_improvement_recommendations

# Set up logging
logger = setup_logging(name='demo.assess', level='INFO')


def assess_sample_dataset():
    """Assess the sample OOI dataset"""

    print("\n" + "="*70)
    print("  OOI FAIR ASSESSMENT DEMO")
    print("="*70 + "\n")

    # Path to sample dataset
    dataset_path = 'data/raw/test_download.nc'

    if not Path(dataset_path).exists():
        print(f"❌ Sample dataset not found: {dataset_path}")
        print("\nPlease run the data extractor first:")
        print("  python3 src/extract/ooi_api.py")
        return

    print(f"Dataset: {dataset_path}\n")

    # ==================================================================
    # Part 1: FAIR Assessment
    # ==================================================================

    print("="*70)
    print("PART 1: FAIR PRINCIPLES ASSESSMENT")
    print("="*70 + "\n")

    assessor = FAIRAssessor(dataset_path)
    score = assessor.assess()

    print("\n" + "="*70)
    print("FAIR SCORE SUMMARY")
    print("="*70)
    print(f"\nTotal Score: {score.total_score:.1f}/100 (Grade: {score.grade})")
    print(f"\nBreakdown:")
    print(f"  F - Findable:       {score.findable_score:.1f}/25  ", end="")
    print_score_bar(score.findable_score, 25)
    print(f"  A - Accessible:     {score.accessible_score:.1f}/20  ", end="")
    print_score_bar(score.accessible_score, 20)
    print(f"  I - Interoperable:  {score.interoperable_score:.1f}/30  ", end="")
    print_score_bar(score.interoperable_score, 30)
    print(f"  R - Reusable:       {score.reusable_score:.1f}/25  ", end="")
    print_score_bar(score.reusable_score, 25)

    # ==================================================================
    # Part 2: Detailed Breakdown
    # ==================================================================

    print("\n" + "="*70)
    print("DETAILED BREAKDOWN")
    print("="*70)

    print("\n📍 FINDABLE Metrics:")
    print_metrics(score.findable_details)

    print("\n🌐 ACCESSIBLE Metrics:")
    print_metrics(score.accessible_details)

    print("\n🔄 INTEROPERABLE Metrics:")
    print_metrics(score.interoperable_details)

    print("\n♻️  REUSABLE Metrics:")
    print_metrics(score.reusable_details)

    # ==================================================================
    # Part 3: Recommendations
    # ==================================================================

    print("\n" + "="*70)
    print("RECOMMENDATIONS FOR IMPROVEMENT")
    print("="*70 + "\n")

    recommendations = get_improvement_recommendations(score)

    for priority, category, items in recommendations:
        print(f"[{priority.upper()}] {category}:")
        for item in items:
            print(f"  • {item}")
        print()

    # ==================================================================
    # Part 4: CF Compliance Check (Optional)
    # ==================================================================

    print("="*70)
    print("PART 2: CF CONVENTIONS COMPLIANCE (Optional)")
    print("="*70 + "\n")

    print("Running detailed CF compliance check...")
    print("(This may take a moment...)\n")

    try:
        cf_checker = CFComplianceChecker(dataset_path)
        cf_checker.run_compliance_check(checker='cf')

        summary = cf_checker.get_summary()

        print(f"CF Compliance Score: {summary['percentage']:.1f}% "
              f"({summary['scored_points']}/{summary['possible_points']} points)")
        print(f"\nIssues Found:")
        print(f"  High Priority:   {summary['high_priority_issues']}")
        print(f"  Medium Priority: {summary['medium_priority_issues']}")
        print(f"  Low Priority:    {summary['low_priority_issues']}")
        print(f"  Total:           {summary['total_issues']}")

        # Show top recommendations
        recommendations = cf_checker.get_recommendations(max_items=5)
        if recommendations:
            print(f"\nTop {len(recommendations)} CF Issues to Fix:")
            for i, (priority, check, message) in enumerate(recommendations, 1):
                print(f"  {i}. [{priority.upper()}] {check}")
                # Truncate long messages
                msg = message[:70] + "..." if len(message) > 70 else message
                print(f"     {msg}")

    except Exception as e:
        print(f"⚠️  CF compliance check failed: {e}")
        print("   This is optional - FAIR assessment still valid")

    # ==================================================================
    # Part 5: Save Report
    # ==================================================================

    print("\n" + "="*70)
    print("SAVING ASSESSMENT REPORT")
    print("="*70 + "\n")

    output_dir = Path('data/assessments')
    output_dir.mkdir(parents=True, exist_ok=True)

    report_path = output_dir / 'fair_assessment_report.json'
    assessor.generate_report(score, output_path=str(report_path))

    print(f"✅ Full report saved to: {report_path}")

    # ==================================================================
    # Summary
    # ==================================================================

    print("\n" + "="*70)
    print("ASSESSMENT COMPLETE")
    print("="*70 + "\n")

    print("Key Findings:")
    print(f"  • Overall FAIR Score: {score.total_score:.1f}/100 (Grade: {score.grade})")

    # Identify weakest area
    scores_map = {
        'Findability': (score.findable_score, 25),
        'Accessibility': (score.accessible_score, 20),
        'Interoperability': (score.interoperable_score, 30),
        'Reusability': (score.reusable_score, 25)
    }

    weakest = min(scores_map.items(), key=lambda x: x[1][0] / x[1][1])
    print(f"  • Weakest Area: {weakest[0]} ({weakest[1][0]:.1f}/{weakest[1][1]})")

    print(f"  • Full report: {report_path}")

    print("\nNext Steps:")
    print("  1. Review the detailed recommendations above")
    print("  2. Run the enrichment pipeline to improve FAIR score")
    print("  3. Re-assess the enriched dataset to measure improvement")

    print("\n" + "="*70 + "\n")


def print_score_bar(score: float, max_score: float, width: int = 20):
    """Print a visual score bar"""
    percentage = score / max_score
    filled = int(percentage * width)
    empty = width - filled

    bar = "█" * filled + "░" * empty
    print(f"[{bar}] {percentage*100:.0f}%")


def print_metrics(metrics):
    """Print formatted metric list"""
    for metric in metrics:
        status_symbol = {
            'pass': '✅',
            'partial': '⚠️ ',
            'fail': '❌',
            'warning': '⚠️ '
        }.get(metric.status, '•')

        print(f"  {status_symbol} {metric.name}: "
              f"{metric.points_earned:.1f}/{metric.points_possible} pts")

        if metric.details:
            print(f"     {metric.details}")

        if metric.issues:
            print(f"     Issues: {', '.join(metric.issues[:2])}")


def quick_assessment(dataset_path: str):
    """Quick assessment without detailed output"""
    assessor = FAIRAssessor(dataset_path)
    score = assessor.assess()

    print(f"\nQuick FAIR Score: {score.total_score:.1f}/100 (Grade: {score.grade})")
    print(f"  F: {score.findable_score:.1f}/25")
    print(f"  A: {score.accessible_score:.1f}/20")
    print(f"  I: {score.interoperable_score:.1f}/30")
    print(f"  R: {score.reusable_score:.1f}/25")

    return score


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Assess specific dataset from command line
        dataset = sys.argv[1]
        if Path(dataset).exists():
            quick_assessment(dataset)
        else:
            print(f"Error: Dataset not found: {dataset}")
    else:
        # Run full demo
        assess_sample_dataset()
