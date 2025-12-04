from fastapi import FastAPI

from fpts.config.settings import Settings
from fpts.utils.logging import setup_logging, get_logger

settings = Settings()
setup_logging(level=settings.log_level)

logger = get_logger(__name__)
app = FastAPI(title=settings.app_name)


@app.get("/health")
def health_check():
    logger.info("Health check endpoint called.")
    return {
        "status": "ok",
        "environment": settings.environment,
        "log_level": settings.log_level,
    }
