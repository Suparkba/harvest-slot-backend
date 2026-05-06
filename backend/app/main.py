from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.core.config import settings
from backend.app.routers.router import api_router
from backend.app.schemas.common_schema import error_response


app = FastAPI(
    title="Harvest Slot API",
    version="1.0.0",
    description="수확예측 기반 과수농가 예약 직배송 API",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    message = detail if isinstance(detail, str) else "request failed"
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(message=message, error=detail),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=error_response(message="internal server error", error=str(exc)),
    )


app.include_router(api_router, prefix=settings.api_v1_prefix)
