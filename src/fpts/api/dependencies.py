from fastapi import Request

from fpts.query.service import QueryService
from fpts.processing.raster_service import RasterService
from fpts.processing.phenology_service import PhenologyComputationService


def get_query_service(request: Request) -> QueryService:
    return request.app.state.query_service


def get_raster_service(request: Request) -> RasterService:
    return request.app.state.raster_service


def get_phenology_compute_service(request: Request) -> PhenologyComputationService:
    return request.app.state.phenology_compute_service
