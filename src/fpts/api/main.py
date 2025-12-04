from fastapi import FastAPI, Query
from datetime import date

from fpts.config.settings import Settings
from fpts.utils.logging import setup_logging, get_logger
from fpts.api.schemas import LocationSchema, PhenologyPointResponse

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
):
    """
    Temporary 'fake' phenology endpoint.

    - Validates input
    - Logs the request
    - Returnsa  mock phenology response

    Later, this will call a QueryService that reads from PostGIS
    """

    logger.info(f"Phenology point query recieved: lat={lat}, lon={lon}, year={year}")

    location = LocationSchema(lat=lat, lon=lon)

    # --- MOCK DATA (will be replaced later) ---
    sos = date(year, 4, 15)
    eos = date(year, 10, 15)
    season_length = (eos - sos).days
    is_forest = True
    # --- END MOCK DATA ---

    return PhenologyPointResponse(
        year=year,
        location=location,
        sos_date=sos,
        eos_date=eos,
        season_length=season_length,
        is_forest=is_forest,
    )
