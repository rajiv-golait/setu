"""Unified error envelope. Every failure path returns this shape.

{ "error": { "code", "message", "details", "retryable" } }
"""
from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings

# Canonical error codes.
VALIDATION_ERROR = "VALIDATION_ERROR"
EXTRACTION_FAILED = "EXTRACTION_FAILED"
REASONING_FAILED = "REASONING_FAILED"
NOT_FOUND = "NOT_FOUND"
RATE_LIMITED = "RATE_LIMITED"
CONSENT_REQUIRED = "CONSENT_REQUIRED"
UNAUTHORIZED = "UNAUTHORIZED"
FORBIDDEN = "FORBIDDEN"
INTERNAL = "INTERNAL"

# Default HTTP status per code.
_STATUS = {
    VALIDATION_ERROR: 422,
    EXTRACTION_FAILED: 502,
    REASONING_FAILED: 502,
    NOT_FOUND: 404,
    RATE_LIMITED: 429,
    CONSENT_REQUIRED: 403,
    UNAUTHORIZED: 401,
    FORBIDDEN: 403,
    INTERNAL: 500,
}


class AppError(Exception):
    """Raise anywhere to produce a clean error envelope response."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        details: dict[str, Any] | None = None,
        retryable: bool = False,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}
        self.retryable = retryable
        self.status_code = status_code or _STATUS.get(code, 500)


def error_body(code: str, message: str, *, details: dict | None = None, retryable: bool = False) -> dict:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
            "retryable": retryable,
        }
    }


def not_found(resource: str, ident: str) -> AppError:
    return AppError(NOT_FOUND, f"{resource} not found", details={"id": ident}, retryable=False)


def register_exception_handlers(app) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(exc.code, exc.message, details=exc.details, retryable=exc.retryable),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content=error_body(
                VALIDATION_ERROR,
                "Request validation failed",
                details={"errors": exc.errors()},
                retryable=False,
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException):
        code = NOT_FOUND if exc.status_code == 404 else INTERNAL
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(code, str(exc.detail), retryable=exc.status_code >= 500),
        )

    @app.exception_handler(SQLAlchemyError)
    async def _db_error(_: Request, exc: SQLAlchemyError):
        hint = None
        if settings.database_url_unresolved:
            hint = "Set SUPABASE_DB_PASSWORD in .env or apps/api/.env"
        else:
            err = str(exc).lower()
            if "password authentication failed" in err:
                hint = "Wrong SUPABASE_DB_PASSWORD — reset it in Supabase Dashboard → Database"
            elif "could not translate host" in err or "name or service not known" in err:
                hint = (
                    "Wrong database host — use direct connection: "
                    "db.sevwzahlsunwqbiowbcx.supabase.co:5432"
                )
        message = "Database connection failed"
        if settings.SECRET_KEY == "dev-only":
            message = f"Database connection failed ({type(exc).__name__})"
        details: dict[str, Any] = {"type": type(exc).__name__}
        if hint:
            details["hint"] = hint
        return JSONResponse(
            status_code=503,
            content=error_body(INTERNAL, message, details=details, retryable=True),
        )

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content=error_body(INTERNAL, "Internal server error", details={"type": type(exc).__name__}, retryable=True),
        )
