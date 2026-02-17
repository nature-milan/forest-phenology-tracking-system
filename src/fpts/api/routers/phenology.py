from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import Literal
from psycopg import Error as PsycopgError

from fpts.api.schemas import (
    LocationSchema,
    PhenologyPointResponse,
    PhenologyTimeseriesResponse,
    PhenologyYearMetricSchema,
    GeoJSONPolygonRequest,
    PhenologyAreaStatsResponse,
    SeasonLengthStat,
)
from fpts.api.dependencies import get_query_service, get_phenology_compute_service
from fpts.domain.models import Location
from fpts.query.service import QueryService
from fpts.utils.logging import get_logger
from fpts.processing.phenology_service import PhenologyComputationService

logger = get_logger(__name__)

router = APIRouter(prefix="/phenology", tags=["phenology"])


@router.get("/point", response_model=PhenologyPointResponse)
def get_point_phenology(
    lat: float = Query(
        ..., ge=-90.0, le=90.0, description="Latitude value for the point."
    ),
    lon: float = Query(
        ..., ge=-180.0, le=180.0, description="Longitude value for the point."
    ),
    year: int = Query(..., ge=2000, le=2027, description="Year we want to analyse."),
    mode: Literal["repo", "compute", "auto"] = Query(
        "repo",
        description="Execution mode - where to fetch metrics from. Return precomputed value from 'repo', 'compute' it as part of request, or try to look up in repo but fall back to computing it with mode = 'auto'",
    ),
    product: str = Query("ndvi_synth", min_length=1, description="Product to analyse."),
    threshold_frac: float = Query(
        0.5,
        gt=0.0,
        lt=1.0,
        description="Fraction value used in calculating SOS and EOS limits.",
    ),
    query_service: QueryService = Depends(get_query_service),
    compute_service: PhenologyComputationService = Depends(
        get_phenology_compute_service
    ),
):
    """
    Get phenology metrics for a single point.

    mode=repo:
      Reads from repository (PostGIS).

    mode=compute:
      Computes from NDVI raster stack on the fly (currently synthetic NDVI stack).

    mode=auto:
      Tries to read from repo, and falls back to compute from NDVI raster stack on the fly (currently synthetic NDVI stack).
    """
    logger.info(
        f"Phenology point query received: lat: {lat}, lon: {lon}, year: {year}, mode: {mode}, product: {product}, threshold_frac: {threshold_frac}"
    )

    location = Location(lat=lat, lon=lon)

    if mode == "repo":
        metric = query_service.get_point_metric(
            product=product, location=location, year=year
        )
        if metric is None:
            raise HTTPException(
                status_code=404,
                detail=f"No phenology data found for product: {product}, location: Location(lat={lat}, lon={lon}) and year: {year}",
            )

    elif mode == "compute":
        try:
            metric = compute_service.compute_point_phenology(
                product=product,
                year=year,
                location=location,
                threshold_frac=threshold_frac,
            )
        except FileNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e

    else:  # mode == "auto"
        metric = query_service.get_point_metric(
            product=product, location=location, year=year
        )
        if metric is None:
            try:
                metric = compute_service.compute_point_phenology(
                    product=product,
                    year=year,
                    location=location,
                    threshold_frac=threshold_frac,
                )
            except FileNotFoundError as e:
                raise HTTPException(status_code=404, detail=str(e)) from e

    return PhenologyPointResponse(
        year=metric.year,
        location=LocationSchema(lat=metric.location.lat, lon=metric.location.lon),
        sos_date=metric.sos_date,
        eos_date=metric.eos_date,
        season_length=metric.season_length,
        is_forest=metric.is_forest,
    )


@router.get(
    "/timeseries",
    response_model=PhenologyTimeseriesResponse,
    responses={
        404: {"description": "No data found"},
        400: {"description": "Invalid parameters"},
    },
)
def get_point_timeseries(
    lat: float = Query(
        ..., ge=-90.0, le=90.0, description="Latitude value for the point."
    ),
    lon: float = Query(
        ..., ge=-180.0, le=180.0, description="Longitude value for the point."
    ),
    start_year: int = Query(
        ..., ge=2000, le=2027, description="Start year (inclusive)."
    ),
    end_year: int = Query(..., ge=2000, le=2027, description="End year (inclusive)."),
    product: str = Query("ndvi_synth", min_length=1, description="Product to analyse."),
    query_service: QueryService = Depends(get_query_service),
):
    logger.info(
        f"Phenology timeseries query received: lat: {lat}, lon: {lon}, start_year: {start_year}, end_year: {end_year}, product: {product}"
    )

    if end_year < start_year:
        raise HTTPException(
            status_code=400, detail="Invalid parameters: end_year must be <= start_year"
        )

    location = Location(lat=lat, lon=lon)

    metrics = query_service.get_point_timeseries(
        product=product,
        location=location,
        start_year=start_year,
        end_year=end_year,
    )

    if not metrics:
        raise HTTPException(
            status_code=404,
            detail=f"No phenology data found for product: {product}, location: {location} and year range {start_year} : {end_year}",
        )

    return PhenologyTimeseriesResponse(
        product=product,
        location=LocationSchema(lat=location.lat, lon=location.lon),
        start_year=start_year,
        end_year=end_year,
        metrics=[
            PhenologyYearMetricSchema(
                year=metric.year,
                sos_date=metric.sos_date,
                eos_date=metric.eos_date,
                season_length=metric.season_length,
                is_forest=metric.is_forest,
            )
            for metric in metrics
        ],
    )


@router.post("/area", response_model=PhenologyAreaStatsResponse)
def get_area_phenology_stats(
    payload: GeoJSONPolygonRequest = Body(...),
    year: int = Query(..., ge=2000, le=2027, description="Year we want to analyse."),
    product: str = Query("ndvi_synth", min_length=1, description="Product to analyse."),
    only_forest: bool = Query(
        False, description="If True, only include forest points."
    ),
    season_length_stat: SeasonLengthStat = Query(
        SeasonLengthStat.mean,
        description="How to summarise season_length: mean, median, or both.",
    ),
    min_season_length: int | None = Query(
        None,
        ge=0,
        le=366,
        description="If set, only include rows with season_length >= this value.",
    ),
    query_service: QueryService = Depends(get_query_service),
):
    logger.info(f"Phenology area query received: year: {year}, product: {product}")

    try:
        stats = query_service.get_area_stats(
            product=product,
            year=year,
            polygon_geojson=payload.geometry,
            only_forest=only_forest,
            min_season_length=min_season_length,
            season_length_stat=season_length_stat.value,
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid GeoJSON geometry")

    if stats is None:
        raise HTTPException(
            status_code=404,
            detail=f"No phenology data found intersecting this polygon for product: {product} and year: {year}",
        )

    print(f"Stats: {stats}")

    return PhenologyAreaStatsResponse(
        product=product,
        year=year,
        n=stats["n"],
        mean_season_length=stats.get("mean_season_length"),
        median_season_length=stats.get("median_season_length"),
        forest_fraction=stats.get("forest_fraction"),
    )
