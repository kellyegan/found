from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import UUID

from sqlmodel import Session

from app.models.image import Image
from app.models.job import ImportJob, ImportJobStatus
from app.repositories.image_repository import ImageRepository
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

    def create_job(self, total_files: int) -> ImportJob:
        """Create and persist a queued import job."""
        return self.job_repo.create(ImportJob(total_files=total_files))

    def process_import(self, job_id: UUID, paths: list[str]) -> None:
        """Run the full import pipeline for a list of paths. Called as a background task."""
        job = self.job_repo.get_by_id(job_id)
        job.status = ImportJobStatus.running
        self.job_repo.update(job)

        successful = duplicate_path_count = duplicate_hash_count = failed = 0

        for path in paths:
            result = self._process_single(path)
            if result == "success":
                successful += 1
            elif result == "duplicate_path":
                duplicate_path_count += 1
            elif result == "duplicate_hash":
                duplicate_hash_count += 1
            else:
                failed += 1

        job = self.job_repo.get_by_id(job_id)
        job.status = ImportJobStatus.completed
        job.processed_files = len(paths)
        job.successful_imports = successful
        job.duplicate_paths = duplicate_path_count
        job.duplicate_hashes = duplicate_hash_count
        job.failed_imports = failed
        job.completed_date = datetime.now(timezone.utc)
        self.job_repo.update(job)

    def _process_single(self, path: str) -> str:
        """Import one file. Returns 'success', 'duplicate_path', 'duplicate_hash', or 'failed'."""
        try:
            if self.image_repo.get_by_path(path):
                return "duplicate_path"

            hash_value = sha256(path)

            if self.image_repo.get_by_hash(hash_value):
                return "duplicate_hash"

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
            )
            self.image_repo.create(image)
            return "success"

        except (UnsupportedFileTypeError, FileNotFoundError, OSError):
            return "failed"
        except Exception:
            return "failed"
