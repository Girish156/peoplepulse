"""
Custom exception hierarchy and FastAPI exception handler registration.
"""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class PeoplePulseException(Exception):
    """Base exception for all PeoplePulse domain errors."""

    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"

    def __init__(self, message: str, error_code: str | None = None):
        self.message = message
        if error_code is not None:
            self.error_code = error_code
        super().__init__(message)

    def to_dict(self):
        return {"error": self.error_code, "message": self.message}


# ---------------------------------------------------------------------------
# Concrete exceptions
# ---------------------------------------------------------------------------

class NotFoundError(PeoplePulseException):
    """Resource not found (maps to HTTP 404)."""

    status_code = 404
    error_code = "NOT_FOUND"


class ConflictError(PeoplePulseException):
    """Resource conflict — e.g. duplicate IDs (maps to HTTP 409)."""

    status_code = 409
    error_code = "CONFLICT"


class PermissionDeniedError(PeoplePulseException):
    """Caller lacks the required permission (maps to HTTP 403)."""

    status_code = 403
    error_code = "PERMISSION_DENIED"


class ValidationError(PeoplePulseException):
    """Input failed domain-level validation (maps to HTTP 422)."""

    status_code = 422
    error_code = "VALIDATION_ERROR"


class ClosedCycleError(PeoplePulseException):
    """
    Attempted to mutate a record that belongs to a closed or archived review
    cycle.  All modifications to closed cycles are prohibited unless performed
    via an authorised admin correction workflow (maps to HTTP 409).
    """

    status_code = 409
    error_code = "CLOSED_CYCLE"

    def __init__(self, cycle_id: str | None = None, message: str | None = None):
        if message is None:
            suffix = f" (cycle: {cycle_id})" if cycle_id else ""
            message = (
                f"Cannot modify records belonging to a closed or archived review "
                f"cycle{suffix}.  Use the admin correction workflow to apply "
                f"authorised changes."
            )
        super().__init__(message)


class BusinessRuleError(PeoplePulseException):
    """General business rule violation (maps to HTTP 400)."""

    status_code = 400
    error_code = "BUSINESS_RULE_VIOLATION"


# ---------------------------------------------------------------------------
# FastAPI handler registration
# ---------------------------------------------------------------------------

def register_exception_handlers(app: FastAPI) -> None:
    """
    Attach global exception handlers to *app*.

    Call this once during application startup::

        register_exception_handlers(app)
    """

    @app.exception_handler(PeoplePulseException)
    async def peoplepulse_exception_handler(
        request: Request, exc: PeoplePulseException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict(),
        )

    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"error": "NOT_FOUND", "message": "The requested resource was not found."},
        )

    @app.exception_handler(405)
    async def method_not_allowed_handler(request: Request, exc) -> JSONResponse:
        return JSONResponse(
            status_code=405,
            content={"error": "METHOD_NOT_ALLOWED", "message": "Method not allowed."},
        )
