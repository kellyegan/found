from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple
from uuid import UUID

from sqlmodel import Session

from app.models.image import Image
from app.models.import_result import ImportResult, ImportResultOutcome
from app.models.job import ImportJob, ImportJobStatus
from app.repositories.image_repository import ImageRepository
from app.repositories.import_result_repository import ImportResultRepository
from app.repositories.job_repository import JobRepository
from app.core.config import settings
from app.services.metadata_service import UnsupportedFileTypeError, extract_metadata
from app.services.thumbnail_service import generate_thumbnail
from app.utils.hashing import sha256


class ImportService:
    """Orchestrates bulk image imports: creates jobs, detects duplicates, extracts metadata."""

    def __init__(self, session: Session):
        self.session = session
        self.image_repo = ImageRepository(session)
        self.job_repo = JobRepository(session)
        self.result_repo = ImportResultRepository(session)

    def create_job(self, total_files: int) -> ImportJob:
        """Create and persist a queued import job."""
        return self.job_repo.create(ImportJob(total_files=total_files))

    def process_import(self, job_id: UUID, paths: list[str]) -> None:
        """Run the full import pipeline for a list of paths. Called as a background task."""
        job = self.job_repo.get_by_id(job_id)
        job.status = ImportJobStatus.running
        self.job_repo.update(job)

        for path in paths:
            outcome, existing_image = self._process_single(path, job_id)

            job = self.job_repo.get_by_id(job_id)
            job.processed_files += 1
            if outcome == "success":
                job.successful_imports += 1
            elif outcome == "duplicate_path":
                job.duplicate_paths += 1
            elif outcome == "duplicate_hash":
                job.duplicate_hashes += 1
            else:
                job.failed_imports += 1
            self.job_repo.update(job)

        job = self.job_repo.get_by_id(job_id)
        job.status = ImportJobStatus.completed
        job.completed_date = datetime.now(timezone.utc)
        self.job_repo.update(job)

    def _process_single(self, path: str, job_id: UUID) -> Tuple[str, Optional[Image]]:
        """Import one file. Returns (outcome, existing_image_or_None).
        Outcome is one of: 'success', 'duplicate_path', 'duplicate_hash', 'failed'."""
        try:
            if self.image_repo.get_by_path(path):
                return "duplicate_path", None

            hash_value = sha256(path)
            existing = self.image_repo.get_by_hash(hash_value)
            if existing:
                self.result_repo.create(ImportResult(
                    job_id=job_id,
                    path=path,
                    outcome=ImportResultOutcome.duplicate_hash,
                    existing_image_id=existing.id,
                ))
                return "duplicate_hash", existing

            meta = extract_metadata(path)

            try:
                thumb_path = generate_thumbnail(path, hash_value, settings.thumbnail_dir)
            except Exception:
                thumb_path = None

            image = Image(
                filename=Path(path).name,
                path=path,
                width=meta.width,
                height=meta.height,
                file_size=meta.file_size,
                mime_type=meta.mime_type,
                sha256_hash=hash_value,
                thumbnail_path=thumb_path,
                import_job_id=job_id,
            )
            self.image_repo.create(image)
            return "success", None

        except (UnsupportedFileTypeError, FileNotFoundError, OSError):
            self.result_repo.create(ImportResult(
                job_id=job_id,
                path=path,
                outcome=ImportResultOutcome.failed,
            ))
            return "failed", None
        except Exception:
            self.result_repo.create(ImportResult(
                job_id=job_id,
                path=path,
                outcome=ImportResultOutcome.failed,
            ))
            return "failed", None
