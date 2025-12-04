from abc import ABC, abstractmethod
from typing import Optional

from fpts.domain.models import Location, PhenologyMetric


class PhenologyRepository(ABC):
    """
    Abstract interface for storing and retrieving phenology metrics.

    Later we'll add a concrete implementation using Postgres/ PostGIS.
    For now, this is just a contract used by services.

    To add:
    - get_timeseries_for_location
    - get_area_stats
    - upsert_metrics
    """

    @abstractmethod
    def get_metric_for_location(
        self, location: Location, year: int
    ) -> Optional[PhenologyMetric]:
        """
        Return phenology metrics for a single location and year,
        or None if no data is available.
        """
        raise NotImplementedError
