from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from fpts.domain.models import Location, PhenologyMetric


class PhenologyRepository(ABC):
    """
    Abstract interface for storing and retrieving phenology metrics.

    To add:
    - get_timeseries_for_location
    - get_area_stats
    - upsert_metrics
    """

    @abstractmethod
    def get_metric_for_location(
        self, *, product: str, location: Location, year: int
    ) -> Optional[PhenologyMetric]:
        """
        Return phenology metrics for a single product, location and year,
        or None if no data is available.
        """
        raise NotImplementedError

    @abstractmethod
    def get_timeseries_for_location(
        self,
        *,
        product: str,
        location: Location,
        start_year: int,
        end_year: int,
    ) -> list[PhenologyMetric]:
        """
        Return metrics for a single product and location across a year range (inclusive).
        Returns an empty list if no data is available.
        """
        raise NotImplementedError

    @abstractmethod
    def get_area_stats(
        self,
        *,
        product: str,
        year: int,
        polygon_geojson: dict,
    ) -> dict | None:
        """
        Aggregate stats for points intersecting polygon.
        Returns None if no rows matched.
        """
        raise NotImplementedError
