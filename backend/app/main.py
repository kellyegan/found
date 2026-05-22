from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1 import router as v1_router
from app.core.database import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="IMGORG API", lifespan=lifespan)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if isinstance(exc.detail, dict) and "code" in exc.detail:
        error = exc.detail
    else:
        error = {"code": "error", "message": str(exc.detail)}
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": error},
    )


app.include_router(v1_router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "ok"}
