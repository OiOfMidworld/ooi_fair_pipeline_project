"""
FAIR Pipeline REST API

Lightweight FastAPI service exposing the OOI / BGC-Argo
assessment and enrichment pipeline.

Start with:
    uvicorn api.main:app --reload --port 8000
"""

import sys
import json
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import List

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import xarray as xr

# Add project root to path so we can import src modules
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from assess.fair_assessor import FAIRAssessor
from transform.enrichment_pipeline import FAIREnrichmentPipeline
from transform.argo_enrichment_pipeline import ArgoEnrichmentPipeline

from api.models import (
    FAIRScoreResponse,
    MetricScoreResponse,
    AssessmentResult,
    AssessAndEnrichResult,
    EnrichmentChange,
    HistoryResponse,
)

# ---------------------------------------------------------------------------
# Directories
# ---------------------------------------------------------------------------
UPLOAD_DIR = PROJECT_ROOT / "data" / "uploads"
ENRICHED_DIR = PROJECT_ROOT / "data" / "enriched"
HISTORY_FILE = PROJECT_ROOT / "data" / "assessment_history.json"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ENRICHED_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="FAIR Pipeline API",
    description="Assess and enrich oceanographic NetCDF datasets for FAIR compliance",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _save_upload(upload: UploadFile) -> Path:
    """Persist an uploaded file and return its path."""
    dest = UPLOAD_DIR / upload.filename
    with open(dest, "wb") as f:
        shutil.copyfileobj(upload.file, f)
    return dest


def _detect_dataset_type(path: Path) -> str:
    """Return 'argo' or 'ooi' based on file contents."""
    ds = xr.open_dataset(path)
    is_argo = "JULD" in ds.variables or "N_PROF" in ds.dims
    ds.close()
    return "argo" if is_argo else "ooi"


def _fair_score_to_response(score) -> FAIRScoreResponse:
    """Convert internal FAIRScore dataclass → Pydantic model."""

    def _metric_list(details) -> List[MetricScoreResponse]:
        return [
            MetricScoreResponse(
                name=m.name,
                points_earned=m.points_earned,
                points_possible=m.points_possible,
                percentage=m.percentage,
                status=m.status,
                details=m.details,
                issues=list(m.issues),
            )
            for m in details
        ]

    return FAIRScoreResponse(
        total_score=round(score.total_score, 2),
        grade=score.grade,
        findable_score=round(score.findable_score, 2),
        accessible_score=round(score.accessible_score, 2),
        interoperable_score=round(score.interoperable_score, 2),
        reusable_score=round(score.reusable_score, 2),
        findable_details=_metric_list(score.findable_details),
        accessible_details=_metric_list(score.accessible_details),
        interoperable_details=_metric_list(score.interoperable_details),
        reusable_details=_metric_list(score.reusable_details),
    )


def _load_history() -> list:
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text())
    return []


def _save_history(records: list):
    HISTORY_FILE.write_text(json.dumps(records, indent=2))


def _append_history(record: dict):
    records = _load_history()
    records.append(record)
    _save_history(records)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/assess", response_model=AssessmentResult)
def assess(file: UploadFile = File(...)):
    """Upload a NetCDF file and get its FAIR score."""
    path = _save_upload(file)
    try:
        dataset_type = _detect_dataset_type(path)
        assessor = FAIRAssessor(str(path))
        score = assessor.assess()
        score_resp = _fair_score_to_response(score)

        result = AssessmentResult(
            filename=file.filename,
            timestamp=datetime.now(timezone.utc).isoformat(),
            dataset_type=dataset_type,
            score=score_resp,
        )

        _append_history(result.model_dump())
        return result

    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/enrich")
def enrich(file: UploadFile = File(...)):
    """Upload a NetCDF file and download the enriched version."""
    path = _save_upload(file)
    try:
        dataset_type = _detect_dataset_type(path)
        enriched_path = ENRICHED_DIR / f"{path.stem}_enriched.nc"

        if dataset_type == "argo":
            pipeline = ArgoEnrichmentPipeline(str(path), str(enriched_path))
        else:
            pipeline = FAIREnrichmentPipeline(str(path), str(enriched_path))

        pipeline.run()
        pipeline.save()

        return FileResponse(
            enriched_path,
            media_type="application/x-netcdf",
            filename=enriched_path.name,
        )

    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/assess-and-enrich", response_model=AssessAndEnrichResult)
def assess_and_enrich(file: UploadFile = File(...)):
    """Upload, assess original, enrich, assess enriched, return comparison."""
    path = _save_upload(file)
    try:
        dataset_type = _detect_dataset_type(path)

        # Assess original
        assessor_orig = FAIRAssessor(str(path))
        original_score = assessor_orig.assess()

        # Enrich
        enriched_path = ENRICHED_DIR / f"{path.stem}_enriched.nc"
        if dataset_type == "argo":
            pipeline = ArgoEnrichmentPipeline(str(path), str(enriched_path))
        else:
            pipeline = FAIREnrichmentPipeline(str(path), str(enriched_path))

        pipeline.run()
        pipeline.save()
        summary = pipeline.get_enrichment_summary()

        # Assess enriched
        assessor_enr = FAIRAssessor(str(enriched_path))
        enriched_score = assessor_enr.assess()

        orig_resp = _fair_score_to_response(original_score)
        enr_resp = _fair_score_to_response(enriched_score)

        changes = [
            EnrichmentChange(
                enricher=name,
                changes_made=info["changes_made"],
                issues_found=info["issues_found"],
            )
            for name, info in summary.get("enrichers", {}).items()
        ]

        result = AssessAndEnrichResult(
            filename=file.filename,
            dataset_type=dataset_type,
            original_score=orig_resp,
            enriched_score=enr_resp,
            improvement=round(enriched_score.total_score - original_score.total_score, 2),
            enrichment_changes=changes,
            enriched_filename=enriched_path.name,
        )

        # Store both original and enriched in history
        _append_history({
            "filename": file.filename,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "dataset_type": dataset_type,
            "original_score": orig_resp.model_dump(),
            "enriched_score": enr_resp.model_dump(),
            "improvement": result.improvement,
        })

        return result

    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.get("/history", response_model=HistoryResponse)
def history():
    """Return assessment history."""
    records = _load_history()

    orig_scores = []
    enr_scores = []
    assessments = []

    for r in records:
        # Handle both formats (assess-only and assess-and-enrich)
        if "original_score" in r:
            orig_scores.append(r["original_score"]["total_score"])
            enr_scores.append(r["enriched_score"]["total_score"])
            assessments.append(AssessmentResult(
                filename=r["filename"],
                timestamp=r["timestamp"],
                dataset_type=r["dataset_type"],
                score=FAIRScoreResponse(**r["enriched_score"]),
            ))
        elif "score" in r:
            orig_scores.append(r["score"]["total_score"])
            assessments.append(AssessmentResult(
                filename=r["filename"],
                timestamp=r["timestamp"],
                dataset_type=r["dataset_type"],
                score=FAIRScoreResponse(**r["score"]),
            ))

    return HistoryResponse(
        assessments=assessments,
        total_processed=len(assessments),
        average_original_score=round(sum(orig_scores) / len(orig_scores), 2) if orig_scores else None,
        average_enriched_score=round(sum(enr_scores) / len(enr_scores), 2) if enr_scores else None,
    )


@app.get("/download/{filename}")
def download_enriched(filename: str):
    """Download an enriched file by name."""
    path = ENRICHED_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, media_type="application/x-netcdf", filename=filename)
