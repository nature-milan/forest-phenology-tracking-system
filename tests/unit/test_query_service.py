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


def test_query_service_timeseries_returns_sorted_metrics():
    repo = InMemoryPhenologyRepository()
    service = QueryService(repository=repo)

    loc = Location(lat=52.5, lon=13.4)

    m2019 = PhenologyMetric(
        year=2019,
        location=loc,
        sos_date=date(2019, 4, 10),
        eos_date=date(2019, 10, 10),
        season_length=(date(2019, 10, 10) - date(2019, 4, 10)).days,
        is_forest=True,
    )
    m2021 = PhenologyMetric(
        year=2021,
        location=loc,
        sos_date=date(2021, 4, 20),
        eos_date=date(2021, 10, 20),
        season_length=(date(2021, 10, 20) - date(2021, 4, 20)).days,
        is_forest=True,
    )

    repo.add_metric(product="test_product", metric=m2021)
    repo.add_metric(product="test_product", metric=m2019)

    result = service.get_point_timeseries(
        product="test_product", location=loc, start_year=2018, end_year=2022
    )
    assert [m.year for m in result] == [2019, 2021]
