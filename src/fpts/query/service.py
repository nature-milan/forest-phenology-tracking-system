from typing import Optional

from fpts.domain.models import Location, PhenologyMetric
from fpts.storage.phenology_repository import PhenologyRepository


class QueryService:
    """
    Application service for read-only phenology queries.

    The API layer will depend on this service instead of talking
    to repositories or storage directly.
    """

    def __init__(self, repository: PhenologyRepository) -> None:
        self._repository = repository

    def get_point_metric(
        self, location: Location, year: int
    ) -> Optional[PhenologyMetric]:
        """
        Return phenology metric for a single location and year, or None if not found
        """
        return self._repository.get_metric_for_location(location, year)
