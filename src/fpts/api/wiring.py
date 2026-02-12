from fpts.config.settings import Settings

from fpts.query.service import QueryService
from fpts.processing.raster_service import RasterService
from fpts.processing.phenology_service import PhenologyComputationService

from fpts.storage.local_raster_repository import LocalRasterRepository
from fpts.storage.in_memory_repository import InMemoryPhenologyRepository
from fpts.storage.postgis_phenology_repository import PostGISPhenologyRepository


def wire_in_memory_services(app, settings: Settings) -> None:
    """
    Wiring for development/testing.
    """
    # Local raster repo to read from.
    app.state.raster_repo = LocalRasterRepository(data_dir=settings.data_dir)
    app.state.raster_service = RasterService(raster_repo=app.state.raster_repo)
    app.state.phenology_compute_service = PhenologyComputationService(
        raster_repo=app.state.raster_repo
    )

    # In memory phenology repo to store and read metrics.
    repo = InMemoryPhenologyRepository()
    app.state.phenology_repo = repo
    app.state.query_service = QueryService(repository=repo)


def wire_postgis_services(app, settings: Settings) -> None:
    """
    Wiring for Production.
    """
    # Local raster repo to read from.
    app.state.raster_repo = LocalRasterRepository(data_dir=settings.data_dir)
    app.state.raster_service = RasterService(raster_repo=app.state.raster_repo)
    app.state.phenology_compute_service = PhenologyComputationService(
        raster_repo=app.state.raster_repo
    )

    # PostGIS repo to store and read metrics.
    repo = PostGISPhenologyRepository(dsn=settings.database_dsn)
    app.state.phenology_repo = repo
    app.state.query_service = QueryService(repository=repo)
