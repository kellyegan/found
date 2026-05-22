from fastapi import APIRouter

from app.api.v1 import images, jobs

router = APIRouter()
router.include_router(images.router)
router.include_router(jobs.router)
