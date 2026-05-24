from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.core.database import get_session
from app.repositories.import_result_repository import ImportResultRepository
from app.repositories.job_repository import JobRepository
from app.schemas.job import ImportJobRead, ImportResultRead

router = APIRouter(tags=["Import Jobs"])


def _get_repo(session: Session = Depends(get_session)) -> JobRepository:
    return JobRepository(session)


def _get_result_repo(session: Session = Depends(get_session)) -> ImportResultRepository:
    return ImportResultRepository(session)


def _build_job_read(job, result_repo: ImportResultRepository) -> dict:
    results = [ImportResultRead.model_validate(r) for r in result_repo.list_by_job(job.id)]
    data = ImportJobRead.model_validate(job).model_dump()
    data["results"] = [r.model_dump() for r in results]
    return data


@router.get("/jobs", summary="List import jobs")
def list_jobs(
    repo: JobRepository = Depends(_get_repo),
    result_repo: ImportResultRepository = Depends(_get_result_repo),
):
    """Return all import jobs ordered newest first, including per-path results for each."""
    return {
        "success": True,
        "data": [_build_job_read(j, result_repo) for j in repo.list()],
    }


@router.get("/jobs/{job_id}", summary="Get import job")
def get_job(
    job_id: UUID,
    repo: JobRepository = Depends(_get_repo),
    result_repo: ImportResultRepository = Depends(_get_result_repo),
):
    """Retrieve the status, progress, and per-path results of a single import job."""
    job = repo.get_by_id(job_id)
    if not job:
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": "Job not found."},
        )
    return {"success": True, "data": _build_job_read(job, result_repo)}
