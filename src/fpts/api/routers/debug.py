from fastapi import APIRouter, Depends, HTTPException, Query

from fpts.domain.models import Location
from fpts.processing.raster_service import RasterService
from fpts.api.dependencies import get_raster_service
from fpts.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/raster-sample")
def raster_sample(
    product: str = Query(..., min_length=1),
    year: int = Query(..., ge=1900, le=2100),
    lat: float = Query(..., ge=-90.0, le=90.0),
    lon: float = Query(..., ge=-180.0, le=180.0),
    raster_service: RasterService = Depends(get_raster_service),
):
    """
    Debug endpoint to verify raster sampling end-to-end.

    Returns the sampled pixel value from the raster for (product, year) at (lat, lon).
    """
    logger.info(
        f"Raster sample requested: product: {product}, year: {year}, lat: {lat}, lon: {lon}"
    )

    try:
        location = Location(lat=lat, lon=lon)
        value = raster_service.sample_point(
            product=product, year=year, location=location
        )
        return {
            "product": product,
            "year": year,
            "location": {"lat": lat, "lon": lon},
            "value": value,
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
