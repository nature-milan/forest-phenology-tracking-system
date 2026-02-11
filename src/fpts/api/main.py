from fastapi import FastAPI

from fpts.config.settings import Settings
from fpts.utils.logging import setup_logging, get_logger
from fpts.api.routers.phenology import router as phenology_router
from fpts.api.routers.debug import router as debug_router
from fpts.api.wiring import wire_in_memory_services, wire_postgis_services

logger = get_logger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    setup_logging(level=settings.log_level)

    app = FastAPI(title=settings.app_name)

    if settings.phenology_repo_backend == "postgis":
        wire_postgis_services(app, settings=settings)
    else:
        wire_in_memory_services(app, settings=settings)

    # Routers
    app.include_router(phenology_router)
    app.include_router(debug_router)

    @app.get("/health")
    def health_check():
        logger.info("Health check endpoint called.")
        return {
            "status": "ok",
            "environment": settings.environment,
            "log_level": settings.log_level,
        }

    return app


app = create_app()
