from fpts.cache.ttl_cache import InMemoryTTLCache
from fpts.config.settings import Settings
from fpts.domain.models import PhenologyMetric
from fpts.processing.phenology_service import PhenologyComputationService
from fpts.processing.raster_service import RasterService
from fpts.query.service import QueryService
from fpts.storage.in_memory_repository import InMemoryPhenologyRepository
from fpts.storage.local_raster_repository import LocalRasterRepository
from fpts.storage.postgis_phenology_repository import PostGISPhenologyRepository


def wire_in_memory_services(app, settings: Settings) -> None:
    """
    Wiring for development/testing.
    """
    # Create cache
    app.state.point_metric_cache = InMemoryTTLCache[str, PhenologyMetric](
        maxsize=50_000,
        ttl_seconds=300.0,
    )

    # Local raster repo to read from.
    app.state.raster_repo = LocalRasterRepository(data_dir=settings.data_dir)
    app.state.raster_service = RasterService(raster_repo=app.state.raster_repo)
    app.state.phenology_compute_service = PhenologyComputationService(
        raster_repo=app.state.raster_repo,
        point_cache=app.state.point_metric_cache,
    )

    # In memory phenology repo to store and read metrics.
    repo = InMemoryPhenologyRepository()
    app.state.phenology_repo = repo
    app.state.query_service = QueryService(repository=repo)


def wire_postgis_services(app, settings: Settings) -> None:
    """
    Wiring for Production.
    """
    # Create cache
    app.state.point_metric_cache = InMemoryTTLCache[str, PhenologyMetric](
        maxsize=50_000,
        ttl_seconds=300.0,
    )

    # Local raster repo to read from.
    app.state.raster_repo = LocalRasterRepository(data_dir=settings.data_dir)
    app.state.raster_service = RasterService(raster_repo=app.state.raster_repo)
    app.state.phenology_compute_service = PhenologyComputationService(
        raster_repo=app.state.raster_repo,
        point_cache=app.state.point_metric_cache,
    )

    # PostGIS repo to store and read metrics.
    repo = PostGISPhenologyRepository(dsn=settings.database_dsn)
    app.state.phenology_repo = repo
    app.state.query_service = QueryService(repository=repo)
