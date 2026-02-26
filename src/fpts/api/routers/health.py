from fastapi import APIRouter

from fpts.config.settings import Settings
from fpts.utils.logging import get_logger

logger = get_logger(__name__)
settings = Settings()


router = APIRouter()


@router.get("/health")
def health_check():
    logger.info("Health check endpoint called.")
    return {
        "Status": "ok",
        "Environment": settings.environment,
        "Log level": settings.log_level,
        "Phenology repo backend": settings.phenology_repo_backend,
        "Cache backend": settings.cache_backend,
        "Metrics enabled": settings.enable_metrics,
    }
