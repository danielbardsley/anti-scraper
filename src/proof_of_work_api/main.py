from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from proof_of_work_api.config.app_settings import AppSettings
from proof_of_work_api.models.challenge_issue_request import ChallengeIssueRequest
from proof_of_work_api.models.random_numbers_request import RandomNumbersRequest
from proof_of_work_api.services.api_error import ApiError
from proof_of_work_api.services.application_container import ApplicationContainer


def create_app() -> FastAPI:
    settings = AppSettings()
    container = ApplicationContainer(settings)

    app = FastAPI(title="Proof-of-Work Demo", version="0.2.0")
    app.state.container = container
    app.mount("/static", StaticFiles(directory=settings.web_root), name="static")

    @app.exception_handler(ApiError)
    async def api_error_handler(_: Request, error: ApiError) -> JSONResponse:
        container.telemetry_service.increment(f"errors.{error.code}")
        return JSONResponse(
            status_code=error.status_code,
            content={
                "error": {
                    "code": error.code,
                    "message": error.message,
                    **error.details,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, error: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "Request validation failed.",
                    "details": error.errors(),
                }
            },
        )

    @app.get("/")
    async def index() -> FileResponse:
        return FileResponse(settings.web_root / "index.html")

    @app.get("/healthz")
    async def healthz() -> dict:
        return {
            "status": "ok",
            "serverTime": datetime.now(timezone.utc).isoformat(),
        }

    @app.get("/v1/config")
    async def config() -> dict:
        return {
            "defaultCount": settings.default_random_count,
            "minCount": settings.min_random_count,
            "maxCount": settings.max_random_count,
            "requestsPerTier": settings.requests_per_tier,
            "sourceRequestsPerTier": settings.source_requests_per_tier,
            "successWindowSeconds": settings.success_window_seconds,
            "maxOutstandingChallenges": settings.max_outstanding_challenges,
            "sessionCookieName": settings.session_cookie_name,
        }

    @app.get("/v1/telemetry")
    async def telemetry() -> dict:
        return {
            "counters": container.telemetry_service.snapshot(),
        }

    @app.post("/v1/pow/challenges")
    async def issue_challenge(request: ChallengeIssueRequest, http_request: Request, http_response: Response) -> dict:
        current_time = datetime.now(timezone.utc)
        issued_ip = container.client_ip_resolver.resolve(http_request)
        existing_session_id = http_request.cookies.get(settings.session_cookie_name)
        session, created = container.session_store.get_or_create(existing_session_id, issued_ip, current_time)
        if created:
            container.telemetry_service.increment("sessions.created")
        if created or existing_session_id != session.session_id:
            http_response.set_cookie(
                key=settings.session_cookie_name,
                value=session.session_id,
                httponly=True,
                samesite="lax",
                secure=settings.secure_cookie,
                max_age=settings.session_idle_ttl_seconds,
                path="/",
            )
        challenge = container.challenge_service.issue_challenge(request, session.session_id, issued_ip)
        container.telemetry_service.increment("challenges.issued")
        container.telemetry_service.increment(f"challenges.issued.ip.{issued_ip}")
        container.telemetry_service.increment(f"challenges.issued.session.{session.session_id}")
        return challenge

    @app.post("/v1/random-numbers")
    async def random_numbers(request: RandomNumbersRequest, http_request: Request) -> dict:
        current_time = datetime.now(timezone.utc)
        source_key = container.client_ip_resolver.resolve(http_request)
        session_id = http_request.cookies.get(settings.session_cookie_name)
        session = container.session_store.get_required(session_id, current_time)
        if session is None:
            raise ApiError(401, "SESSION_REQUIRED", "A valid server-issued session is required.")
        verification = container.proof_verifier.verify_and_consume(request, session.session_id, source_key)
        completed_at = datetime.now(timezone.utc)
        container.session_success_tracker.record(session.session_id, completed_at)
        container.source_success_tracker.record(source_key, completed_at)
        container.telemetry_service.increment("protected.success")
        container.telemetry_service.increment(f"protected.success.tier.{verification['tier']}")
        numbers = container.random_number_service.generate(verification["count"])
        return {
            "numbers": numbers,
            "meta": {
                "count": verification["count"],
                "tier": verification["tier"],
                "stages": verification["stages"],
                "challengeId": verification["challengeId"],
                "sessionId": verification["sessionId"],
                "sourceKey": verification["sourceKey"],
                "completedAt": completed_at.isoformat(),
            },
        }

    return app
