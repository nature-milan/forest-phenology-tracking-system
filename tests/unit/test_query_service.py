from datetime import date

from fpts.domain.models import Location, PhenologyMetric
from fpts.query.service import QueryService
from fpts.storage.in_memory_repository import InMemoryPhenologyRepository


def test_query_service_returns_metric_when_present():
    repo = InMemoryPhenologyRepository()
    service = QueryService(repository=repo)

    loc = Location(lat=52.5, lon=13.4)
    metric = PhenologyMetric(
        year=2020,
        location=loc,
        sos_date=date(2020, 4, 15),
        eos_date=date(2020, 10, 15),
        season_length=(date(2020, 10, 15) - date(2020, 4, 15)).days,
        is_forest=True,
    )

    repo.add_metric(product="test_product", metric=metric)

    result = service.get_point_metric(product="test_product", location=loc, year=2020)

    assert result is not None
    assert result == metric
    assert result.year == 2020
    assert result.location == loc
    assert result.is_forest is True


def test_query_service_returns_none_when_missing():
    repo = InMemoryPhenologyRepository()
    service = QueryService(repository=repo)

    loc = Location(lat=0.0, lon=0.0)
    result = service.get_point_metric(product="test_product", location=loc, year=2020)

    assert result is None
