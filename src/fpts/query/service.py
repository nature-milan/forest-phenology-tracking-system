from typing import Optional

from fpts.domain.models import Location, PhenologyMetric
from fpts.storage.phenology_repository import PhenologyRepository


class QueryService:
    """
    Application service for read-only phenology queries.

    The API layer will depend on this service instead of talking
    to repositories or storage directly.

    Returns metrics for a point (lat, long, year)
    """

    def __init__(self, repository: PhenologyRepository) -> None:
        self._repository = repository

    def get_point_metric(
        self, product: str, location: Location, year: int
    ) -> Optional[PhenologyMetric]:
        """
        Return phenology metric for a single location and year, or None if not found
        """
        return self._repository.get_metric_for_location(
            product=product, location=location, year=year
        )

    def get_point_timeseries(
        self,
        *,
        product: str,
        location: Location,
        start_year: int,
        end_year: int,
    ) -> list[PhenologyMetric]:
        return self._repository.get_timeseries_for_location(
            product=product,
            location=location,
            start_year=start_year,
            end_year=end_year,
        )
