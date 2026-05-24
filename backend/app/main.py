import sys
from pathlib import Path

# When run directly (python app/main.py), Python puts backend/app/ on sys.path
# instead of backend/. Fix it so `import app` resolves correctly either way.
_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1 import router as v1_router
from app.core.database import run_migrations


@asynccontextmanager
async def lifespan(app: FastAPI):
    run_migrations()
    yield


app = FastAPI(title="Found API", lifespan=lifespan)

# Allow any localhost origin so the desktop GUI and browser extension can reach
# the API without CORS errors. The server binds to 127.0.0.1 so this is safe.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    first = exc.errors()[0]
    field = " → ".join(str(p) for p in first["loc"])
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {"code": "validation_error", "message": f"{field}: {first['msg']}"},
        },
    )


app.include_router(v1_router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
