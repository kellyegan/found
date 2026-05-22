from typing import List, Optional
from uuid import UUID

from sqlmodel import Session, select

from app.models.job import ImportJob


class JobRepository:
    """DB access layer for ImportJob records. All methods commit and refresh before returning."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, job: ImportJob) -> ImportJob:
        """Persist a new job and return it with its generated ID."""
        self.session.add(job)
        self.session.commit()
        self.session.refresh(job)
        return job

    def get_by_id(self, job_id: UUID) -> Optional[ImportJob]:
        """Return the job with the given ID, or None if not found."""
        return self.session.get(ImportJob, job_id)

    def list(self) -> List[ImportJob]:
        """Return all jobs ordered newest first."""
        return list(
            self.session.exec(
                select(ImportJob).order_by(ImportJob.created_date.desc())
            ).all()
        )

    def update(self, job: ImportJob) -> ImportJob:
        """Persist changes to an existing job and return the refreshed record."""
        self.session.add(job)
        self.session.commit()
        self.session.refresh(job)
        return job
