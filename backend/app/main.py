from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api.v1 import router as v1_router
from app.core.database import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="IMGORG API", lifespan=lifespan)

app.include_router(v1_router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "ok"}
