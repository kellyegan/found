from typing import List
from uuid import UUID

from sqlmodel import Session, select

from app.models.import_result import ImportResult


class ImportResultRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, result: ImportResult) -> ImportResult:
        self.session.add(result)
        self.session.commit()
        self.session.refresh(result)
        return result

    def list_by_job(self, job_id: UUID) -> List[ImportResult]:
        return list(
            self.session.exec(
                select(ImportResult).where(ImportResult.job_id == job_id)
            ).all()
        )
