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
        "status": "ok",
        "environment": settings.environment,
        "log_level": settings.log_level,
        "phenology_repo_backend": settings.phenology_repo_backend,
        "cache_backend": settings.cache_backend,
        "enable_metrics": settings.enable_metrics,
    }
