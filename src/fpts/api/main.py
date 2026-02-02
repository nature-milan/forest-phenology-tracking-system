from fastapi import FastAPI, Query, Depends, HTTPException
from datetime import date

from fpts.config.settings import Settings
from fpts.utils.logging import setup_logging, get_logger
from fpts.api.schemas import LocationSchema, PhenologyPointResponse
from fpts.api.dependencies import get_query_service
from fpts.domain.models import Location
from fpts.query.service import QueryService

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


@app.get("/phenology/point", response_model=PhenologyPointResponse)
def get_point_phenology(
    lat: float = Query(..., ge=-90.0, le=90.0),
    lon: float = Query(..., ge=-180.0, le=180.0),
    year: int = Query(..., ge=2000, le=2100),
    service: QueryService = Depends(get_query_service),
):
    logger.info(f"Phenology point query recieved: lat={lat}, lon={lon}, year={year}")

    location = Location(lat=lat, lon=lon)
    metric = service.get_point_metric(location=location, year=year)

    if metric is None:
        raise HTTPException(
            status_code=404, detail="No phenology data found for this location/year."
        )

    return PhenologyPointResponse(
        year=metric.year,
        location=LocationSchema(lat=metric.location.lat, lon=metric.location.lon),
        sos_date=metric.sos_date,
        eos_date=metric.eos_date,
        season_length=metric.season_length,
        is_forest=metric.is_forest,
    )
