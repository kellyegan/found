from fastapi import APIRouter

from app.api.v1 import categories, collections, images, jobs, tags

router = APIRouter()
router.include_router(images.router)
router.include_router(jobs.router)
router.include_router(tags.router)
router.include_router(categories.router)
router.include_router(collections.router)
