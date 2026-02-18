from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from fpts.config.settings import Settings
from fpts.domain.models import Location, PhenologyMetric
from fpts.processing.phenology_service import PhenologyComputationService
from fpts.storage.local_raster_repository import LocalRasterRepository
from fpts.storage.postgis_phenology_repository import PostGISPhenologyRepository


@dataclass(frozen=True)
class GridSpec:
    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float
    step_deg: float


def iter_grid(spec: GridSpec) -> Iterable[Location]:
    lat = spec.min_lat
    while lat <= spec.max_lat + 1e-12:
        lon = spec.min_lon
        while lon <= spec.max_lon + 1e-12:
            yield Location(lat=lat, lon=lon)
            lon += spec.step_deg
        lat += spec.step_deg


def process_year_to_db(
    *,
    settings: Settings,
    product: str,
    year: int,
    grid: GridSpec,
) -> int:

    raster_repo = LocalRasterRepository(data_dir=settings.data_dir)
    compute = PhenologyComputationService(raster_repo=raster_repo)
    db_repo = PostGISPhenologyRepository(dsn=settings.database_dsn)

    n = 0
    for loc in iter_grid(grid):
        metric: PhenologyMetric = compute.compute_point_phenology(
            product=product, location=loc, year=year
        )
        db_repo.upsert(product=product, metric=metric)
        n += 1
    return n
