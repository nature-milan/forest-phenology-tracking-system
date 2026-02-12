from typing import Optional, Tuple

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
