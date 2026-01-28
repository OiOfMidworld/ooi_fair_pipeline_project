"""
Pydantic response models for the FAIR Pipeline API.

Mirrors the existing FAIRScore / MetricScore dataclasses
so they serialize cleanly to JSON.
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class MetricScoreResponse(BaseModel):
    name: str
    points_earned: float
    points_possible: float
    percentage: float
    status: str
    details: str = ""
    issues: List[str] = []


class FAIRScoreResponse(BaseModel):
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
    score: FAIRScoreResponse


class EnrichmentChange(BaseModel):
    enricher: str
    changes_made: int
    issues_found: int


class AssessAndEnrichResult(BaseModel):
    filename: str
    dataset_type: str
    original_score: FAIRScoreResponse
    enriched_score: FAIRScoreResponse
    improvement: float
    enrichment_changes: List[EnrichmentChange] = []
    enriched_filename: str


class HistoryResponse(BaseModel):
    assessments: List[AssessmentResult]
    total_processed: int
    average_original_score: Optional[float] = None
    average_enriched_score: Optional[float] = None
