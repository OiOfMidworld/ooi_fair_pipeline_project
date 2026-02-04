"""
Pydantic response models for the MRV Pipeline API.

The MRV Readiness Score measures how well a dataset meets
verification requirements for marine carbon dioxide removal (mCDR):
- Is the data findable and citable? (Findable)
- Can verifiers access it with clear terms? (Accessible)
- Does it follow standard formats? (Interoperable)
- Is provenance and quality documented? (Reusable)
"""

from pydantic import BaseModel
from typing import List, Optional


class MetricScoreResponse(BaseModel):
    name: str
    points_earned: float
    points_possible: float
    percentage: float
    status: str
    details: str = ""
    issues: List[str] = []


class MRVScoreResponse(BaseModel):
    """
    MRV Readiness Score breakdown.

    Measures standalone file quality for verification purposes.
    Based on FAIR principles but focused on mCDR/MRV use cases.
    """
    total_score: float
    grade: str
    findable_score: float
    accessible_score: float
    interoperable_score: float
    reusable_score: float
    findable_details: List[MetricScoreResponse] = []
    accessible_details: List[MetricScoreResponse] = []
    interoperable_details: List[MetricScoreResponse] = []
    reusable_details: List[MetricScoreResponse] = []


class AssessmentResult(BaseModel):
    filename: str
    timestamp: str
    dataset_type: str  # "ooi" or "argo"
    score: MRVScoreResponse


class EnrichmentChange(BaseModel):
    enricher: str
    changes_made: int
    issues_found: int


class AssessAndEnrichResult(BaseModel):
    filename: str
    dataset_type: str
    original_score: MRVScoreResponse
    enriched_score: MRVScoreResponse
    improvement: float
    enrichment_changes: List[EnrichmentChange] = []
    enriched_filename: str


class HistoryResponse(BaseModel):
    assessments: List[AssessmentResult]
    total_processed: int
    average_original_score: Optional[float] = None
    average_enriched_score: Optional[float] = None
