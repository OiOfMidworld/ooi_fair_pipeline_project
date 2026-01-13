"""
Unit tests for FAIR metrics and scoring

Tests the scoring rubric, metric calculations, and recommendation engine.
"""

import pytest
from assess.fair_metrics import (
    MetricScore,
    FAIRScore,
    FINDABLE_METRICS,
    ACCESSIBLE_METRICS,
    INTEROPERABLE_METRICS,
    REUSABLE_METRICS,
    calculate_findable_score,
    calculate_accessible_score,
    calculate_interoperable_score,
    calculate_reusable_score,
    get_improvement_recommendations
)


class TestMetricScore:
    """Test MetricScore dataclass"""

    def test_metric_score_creation(self):
        """Test creating a MetricScore"""
        score = MetricScore(
            name='test_metric',
            points_earned=7.5,
            points_possible=10,
            status='partial',
            details='Test details',
            issues=['issue1', 'issue2']
        )

        assert score.name == 'test_metric'
        assert score.points_earned == 7.5
        assert score.points_possible == 10
        assert score.status == 'partial'
        assert len(score.issues) == 2

    def test_metric_percentage_calculation(self):
        """Test percentage property calculation"""
        score = MetricScore(
            name='test',
            points_earned=8,
            points_possible=10,
            status='pass'
        )

        assert score.percentage == 80.0

    def test_metric_percentage_zero_division(self):
        """Test percentage when possible points is 0"""
        score = MetricScore(
            name='test',
            points_earned=0,
            points_possible=0,
            status='pass'
        )

        assert score.percentage == 0.0


class TestFAIRScore:
    """Test FAIRScore dataclass"""

    def test_fair_score_creation(self):
        """Test creating a FAIRScore"""
        score = FAIRScore(
            findable_score=22.5,
            accessible_score=18.0,
            interoperable_score=25.0,
            reusable_score=20.0,
            total_score=85.5
        )

        assert score.findable_score == 22.5
        assert score.accessible_score == 18.0
        assert score.interoperable_score == 25.0
        assert score.reusable_score == 20.0
        assert score.total_score == 85.5

    def test_grade_calculation_a(self):
        """Test grade A (90+)"""
        score = FAIRScore(
            findable_score=23,
            accessible_score=19,
            interoperable_score=28,
            reusable_score=23,
            total_score=93
        )
        assert score.grade == 'A'

    def test_grade_calculation_b(self):
        """Test grade B (80-89)"""
        score = FAIRScore(
            findable_score=22,
            accessible_score=18,
            interoperable_score=25,
            reusable_score=20,
            total_score=85
        )
        assert score.grade == 'B'

    def test_grade_calculation_c(self):
        """Test grade C (70-79)"""
        score = FAIRScore(
            findable_score=18,
            accessible_score=15,
            interoperable_score=21,
            reusable_score=18,
            total_score=72
        )
        assert score.grade == 'C'

    def test_grade_calculation_d(self):
        """Test grade D (60-69)"""
        score = FAIRScore(
            findable_score=15,
            accessible_score=12,
            interoperable_score=18,
            reusable_score=15,
            total_score=60
        )
        assert score.grade == 'D'

    def test_grade_calculation_f(self):
        """Test grade F (<60)"""
        score = FAIRScore(
            findable_score=10,
            accessible_score=8,
            interoperable_score=12,
            reusable_score=10,
            total_score=40
        )
        assert score.grade == 'F'


class TestMetricDefinitions:
    """Test that metric definitions are valid"""

    def test_findable_metrics_structure(self):
        """Test FINDABLE_METRICS has correct structure"""
        assert len(FINDABLE_METRICS) == 4
        assert 'unique_identifier' in FINDABLE_METRICS
        assert 'rich_metadata' in FINDABLE_METRICS

        for name, metric in FINDABLE_METRICS.items():
            assert 'points' in metric
            assert 'description' in metric
            assert 'required_attrs' in metric
            assert 'check_type' in metric
            assert isinstance(metric['points'], int)
            assert isinstance(metric['required_attrs'], list)

    def test_accessible_metrics_structure(self):
        """Test ACCESSIBLE_METRICS has correct structure"""
        assert len(ACCESSIBLE_METRICS) == 4
        assert 'contact_info' in ACCESSIBLE_METRICS
        assert 'access_protocol' in ACCESSIBLE_METRICS

    def test_interoperable_metrics_structure(self):
        """Test INTEROPERABLE_METRICS has correct structure"""
        assert len(INTEROPERABLE_METRICS) == 4
        assert 'cf_compliance' in INTEROPERABLE_METRICS
        assert 'standard_vocabulary' in INTEROPERABLE_METRICS

    def test_reusable_metrics_structure(self):
        """Test REUSABLE_METRICS has correct structure"""
        assert len(REUSABLE_METRICS) == 4
        assert 'clear_license' in REUSABLE_METRICS
        assert 'data_provenance' in REUSABLE_METRICS

    def test_total_points_allocation(self):
        """Test that total possible points equals 100"""
        findable_total = sum(m['points'] for m in FINDABLE_METRICS.values())
        accessible_total = sum(m['points'] for m in ACCESSIBLE_METRICS.values())
        interoperable_total = sum(m['points'] for m in INTEROPERABLE_METRICS.values())
        reusable_total = sum(m['points'] for m in REUSABLE_METRICS.values())

        assert findable_total == 25
        assert accessible_total == 20
        assert interoperable_total == 30
        assert reusable_total == 25


class TestScoreCalculations:
    """Test score calculation functions"""

    def test_calculate_findable_score_perfect(self):
        """Test calculating findable score with perfect metrics"""
        metrics = [
            MetricScore('m1', 5, 5, 'pass'),
            MetricScore('m2', 10, 10, 'pass'),
            MetricScore('m3', 5, 5, 'pass'),
            MetricScore('m4', 5, 5, 'pass')
        ]

        score = calculate_findable_score(metrics)
        assert score == 25.0  # 25/25 * 25 = 25

    def test_calculate_findable_score_partial(self):
        """Test calculating findable score with partial metrics"""
        metrics = [
            MetricScore('m1', 2.5, 5, 'partial'),
            MetricScore('m2', 10, 10, 'pass'),
            MetricScore('m3', 5, 5, 'pass'),
            MetricScore('m4', 2.5, 5, 'partial')
        ]

        score = calculate_findable_score(metrics)
        assert score == 20.0  # 20/25 * 25 = 20

    def test_calculate_accessible_score(self):
        """Test calculating accessible score"""
        metrics = [
            MetricScore('m1', 5, 5, 'pass'),
            MetricScore('m2', 5, 5, 'pass'),
            MetricScore('m3', 2.5, 5, 'partial'),
            MetricScore('m4', 5, 5, 'pass')
        ]

        score = calculate_accessible_score(metrics)
        assert score == 17.5  # 17.5/20 * 20 = 17.5

    def test_calculate_interoperable_score(self):
        """Test calculating interoperable score"""
        metrics = [
            MetricScore('m1', 15, 15, 'pass'),
            MetricScore('m2', 5, 5, 'pass'),
            MetricScore('m3', 5, 5, 'pass'),
            MetricScore('m4', 0, 5, 'fail')
        ]

        score = calculate_interoperable_score(metrics)
        assert score == 25.0  # 25/30 * 30 = 25

    def test_calculate_reusable_score(self):
        """Test calculating reusable score"""
        metrics = [
            MetricScore('m1', 5, 5, 'pass'),
            MetricScore('m2', 8, 8, 'pass'),
            MetricScore('m3', 7, 7, 'pass'),
            MetricScore('m4', 5, 5, 'pass')
        ]

        score = calculate_reusable_score(metrics)
        assert score == 25.0  # Perfect score


class TestRecommendations:
    """Test recommendation generation"""

    def test_recommendations_low_findable(self):
        """Test recommendations when findable score is low"""
        score = FAIRScore(
            findable_score=15,  # 60% - low
            accessible_score=18,
            interoperable_score=25,
            reusable_score=22,
            total_score=80
        )

        recommendations = get_improvement_recommendations(score)

        # Should include findability recommendation
        categories = [cat for _, cat, _ in recommendations]
        assert 'Findability' in categories

    def test_recommendations_low_interoperable(self):
        """Test recommendations when interoperable score is low"""
        score = FAIRScore(
            findable_score=23,
            accessible_score=18,
            interoperable_score=18,  # 60% - low
            reusable_score=22,
            total_score=81
        )

        recommendations = get_improvement_recommendations(score)

        # Should include interoperability recommendation
        categories = [cat for _, cat, _ in recommendations]
        assert 'Interoperability' in categories

    def test_recommendations_all_good(self):
        """Test recommendations when all scores are good"""
        score = FAIRScore(
            findable_score=24,  # 96%
            accessible_score=19,  # 95%
            interoperable_score=28,  # 93%
            reusable_score=23,  # 92%
            total_score=94
        )

        recommendations = get_improvement_recommendations(score)

        # Should have minimal or no recommendations
        assert len(recommendations) <= 1

    def test_recommendations_multiple_issues(self):
        """Test recommendations when multiple areas need work"""
        score = FAIRScore(
            findable_score=15,  # 60% - low
            accessible_score=12,  # 60% - low
            interoperable_score=18,  # 60% - low
            reusable_score=15,  # 60% - low
            total_score=60
        )

        recommendations = get_improvement_recommendations(score)

        # Should have recommendations for all areas
        assert len(recommendations) >= 3

    def test_recommendation_priorities(self):
        """Test that recommendations include proper priorities"""
        score = FAIRScore(
            findable_score=10,
            accessible_score=10,
            interoperable_score=10,
            reusable_score=10,
            total_score=40
        )

        recommendations = get_improvement_recommendations(score)

        # Check that priorities are valid
        valid_priorities = ['critical', 'high', 'medium', 'low']
        for priority, category, items in recommendations:
            assert priority in valid_priorities
            assert isinstance(category, str)
            assert isinstance(items, list)


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_zero_score(self):
        """Test handling of zero scores"""
        score = FAIRScore(
            findable_score=0,
            accessible_score=0,
            interoperable_score=0,
            reusable_score=0,
            total_score=0
        )

        assert score.grade == 'F'
        recommendations = get_improvement_recommendations(score)
        assert len(recommendations) >= 4  # All areas need work

    def test_perfect_score(self):
        """Test handling of perfect scores"""
        score = FAIRScore(
            findable_score=25,
            accessible_score=20,
            interoperable_score=30,
            reusable_score=25,
            total_score=100
        )

        assert score.grade == 'A'
        recommendations = get_improvement_recommendations(score)
        assert len(recommendations) == 0  # No improvements needed

    def test_metric_with_no_issues(self):
        """Test metric score with empty issues list"""
        score = MetricScore(
            name='test',
            points_earned=10,
            points_possible=10,
            status='pass',
            issues=[]
        )

        assert len(score.issues) == 0
        assert score.status == 'pass'
