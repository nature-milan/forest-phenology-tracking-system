from datetime import date

from fpts.domain.models import Location, PhenologyMetric
from fpts.query.service import QueryService
from fpts.storage.in_memory_repository import InMemoryPhenologyRepository

# --- TEMP wiring for v0 ---
# We'll later replace this with proper DI and a PostGIS-backed repository.
_repo = InMemoryPhenologyRepository()

# Seed one known point so the endpoint can return "real" data
_seed_location = Location(lat=52.5, lon=13.4)
_repo.add_metric(
    PhenologyMetric(
        year=2020,
        location=_seed_location,
        sos_date=date(2020, 4, 15),
        eos_date=date(2020, 10, 15),
        season_length=(date(2020, 10, 15) - date(2020, 4, 15)).days,
        is_forest=True,
    )
)

_service = QueryService(repository=_repo)


def get_query_service() -> QueryService:
    return _service
