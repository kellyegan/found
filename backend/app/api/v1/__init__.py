from fastapi import APIRouter

from app.api.v1 import images

router = APIRouter()
router.include_router(images.router)
