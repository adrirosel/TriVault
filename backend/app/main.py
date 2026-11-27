"""FastAPI application entrypoint, CORS configuration, and API v1 router registration."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import accounts, auth, categories, transactions
from app.core.config import get_settings


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()
    application = FastAPI(
        title=settings.PROJECT_NAME,
        version="0.1.0",
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        docs_url=f"{settings.API_V1_PREFIX}/docs",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @application.get(f"{settings.API_V1_PREFIX}/health", tags=["health"])
    def healthcheck() -> dict[str, str]:
        """Liveness check endpoint."""
        return {"status": "ok"}

    application.include_router(auth.router, prefix=settings.API_V1_PREFIX)
    application.include_router(accounts.router, prefix=settings.API_V1_PREFIX)
    application.include_router(categories.router, prefix=settings.API_V1_PREFIX)
    application.include_router(transactions.router, prefix=settings.API_V1_PREFIX)

    return application


app = create_app()
