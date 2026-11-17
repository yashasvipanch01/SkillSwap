from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.errors import DomainError
from app.routers import assessments, auth, exchanges, matches, skills, users


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description="Backend for SkillSwap, a peer-to-peer skill exchange platform.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(DomainError)
    async def handle_domain_error(_: Request, error: DomainError) -> JSONResponse:
        headers = {"WWW-Authenticate": "Bearer"} if error.status_code == 401 else None
        return JSONResponse({"detail": error.detail}, status_code=error.status_code, headers=headers)

    @app.get("/health", tags=["meta"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    for router in (
        auth.router,
        users.router,
        skills.router,
        assessments.router,
        matches.router,
        exchanges.router,
    ):
        app.include_router(router)
    return app


app = create_app()
