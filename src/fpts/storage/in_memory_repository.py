from typing import Tuple

from fpts.domain.models import Location, PhenologyMetric
from fpts.storage.phenology_repository import PhenologyRepository

Key = Tuple[str, float, float, int]  # (product, lat, lon, year)


class InMemoryPhenologyRepository(PhenologyRepository):
    """
    - test/ dev backend

    Simple in-memory implementation of PhenologyRepository.

    This is useful for:
    - Early wiring and tests
    - Unit tests where we don't want a real database
    """

    def __init__(self) -> None:
        self._store: dict[Key, PhenologyMetric] = {}

    def add_metric(self, product: str, metric: PhenologyMetric) -> None:
        key: Key = (product, metric.location.lat, metric.location.lon, metric.year)
        self._store[key] = metric

    def get_metric_for_location(
        self, product: str, location: Location, year: int
    ) -> PhenologyMetric | None:
        key: Key = (product, location.lat, location.lon, year)
        return self._store.get(key)

    def get_timeseries_for_location(
        self,
        *,
        product: str,
        location: Location,
        start_year: int,
        end_year: int,
    ) -> list[PhenologyMetric]:
        if end_year < start_year:
            return []

        items: list[tuple[int, PhenologyMetric]] = []
        for (p, lat, lon, year), metric in self._store.items():
            if (
                p == product
                and lat == location.lat
                and lon == location.lon
                and start_year <= year <= end_year
            ):
                items.append((year, metric))

        items.sort(key=lambda t: t[0])
        return [m for _, m in items]

    def get_area_stats(
        self,
        *,
        product: str,
        year: int,
        polygon_geojson: dict,
        season_length_stat: str,
    ) -> dict | None:
        # In-memory repo does not do spatial ops; keep it explicit.
        raise NotImplementedError("Area stats require PostGIS backend")
