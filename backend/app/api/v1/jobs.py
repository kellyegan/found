from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.core.database import get_session
from app.repositories.job_repository import JobRepository
from app.schemas.job import ImportJobRead

router = APIRouter()


def _get_repo(session: Session = Depends(get_session)) -> JobRepository:
    return JobRepository(session)


@router.get("/jobs")
def list_jobs(repo: JobRepository = Depends(_get_repo)):
    jobs = repo.list()
    return {"success": True, "data": [ImportJobRead.model_validate(j) for j in jobs]}


@router.get("/jobs/{job_id}")
def get_job(job_id: UUID, repo: JobRepository = Depends(_get_repo)):
    job = repo.get_by_id(job_id)
    if not job:
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": "Job not found."},
        )
    return {"success": True, "data": ImportJobRead.model_validate(job)}
