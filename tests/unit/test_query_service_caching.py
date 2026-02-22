from datetime import date
from unittest.mock import MagicMock

from fpts.cache.ttl_cache import InMemoryTTLCache
from fpts.domain.models import Location, PhenologyMetric
from fpts.query.service import QueryService


def test_point_metric_cache_hits_avoid_repo_call():
    repo = MagicMock()
    loc = Location(lat=52.5, lon=13.4)

    metric = PhenologyMetric(
        year=2020,
        location=loc,
        sos_date=date(2020, 4, 10),
        eos_date=date(2020, 10, 10),
        season_length=183,
        is_forest=True,
    )
    repo.get_metric_for_location.return_value = metric

    point_cache = InMemoryTTLCache[str, PhenologyMetric](maxsize=100, ttl_seconds=999)

    service = QueryService(repository=repo, point_cache=point_cache)

    r1 = service.get_point_metric(product="p1", location=loc, year=2020)
    r2 = service.get_point_metric(product="p1", location=loc, year=2020)

    assert r1 == r2 == metric
    assert repo.get_metric_for_location.call_count == 1


def test_point_metric_cache_key_includes_year_and_product():
    repo = MagicMock()
    loc = Location(lat=52.5, lon=13.4)

    repo.get_metric_for_location.return_value = PhenologyMetric(
        year=2020,
        location=loc,
        sos_date=None,
        eos_date=None,
        season_length=None,
        is_forest=True,
    )

    point_cache = InMemoryTTLCache[str, PhenologyMetric](maxsize=100, ttl_seconds=999)
    service = QueryService(repository=repo, point_cache=point_cache)

    _ = service.get_point_metric(product="p1", location=loc, year=2020)
    _ = service.get_point_metric(
        product="p1", location=loc, year=2021
    )  # year change => miss

    assert repo.get_metric_for_location.call_count == 2


def test_timeseries_cache_hits_avoid_repo_call():
    repo = MagicMock()
    loc = Location(lat=52.5, lon=13.4)

    m2019 = PhenologyMetric(
        year=2019,
        location=loc,
        sos_date=date(2019, 4, 10),
        eos_date=date(2019, 10, 10),
        season_length=183,
        is_forest=True,
    )
    repo.get_timeseries_for_location.return_value = [m2019]

    cache = InMemoryTTLCache[str, list[PhenologyMetric]](maxsize=100, ttl_seconds=999)
    service = QueryService(repository=repo, timeseries_cache=cache)

    r1 = service.get_point_timeseries(
        product="p1", location=loc, start_year=2018, end_year=2020
    )
    r2 = service.get_point_timeseries(
        product="p1", location=loc, start_year=2018, end_year=2020
    )

    assert r1 == r2 == [m2019]
    assert repo.get_timeseries_for_location.call_count == 1


def test_timeseries_cache_key_includes_year_range():
    repo = MagicMock()
    loc = Location(lat=52.5, lon=13.4)

    repo.get_timeseries_for_location.return_value = []

    cache = InMemoryTTLCache[str, list[PhenologyMetric]](maxsize=100, ttl_seconds=999)
    service = QueryService(repository=repo, timeseries_cache=cache)

    _ = service.get_point_timeseries(
        product="p1", location=loc, start_year=2018, end_year=2020
    )

    _ = service.get_point_timeseries(
        product="p1", location=loc, start_year=2019, end_year=2020  # changed start_year
    )

    assert repo.get_timeseries_for_location.call_count == 2


def test_area_stats_cache_hits_avoid_repo_call():
    repo = MagicMock()
    poly = {
        "type": "Polygon",
        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
    }
    repo.get_area_stats.return_value = {"n": 10, "mean_season_length": 123.0}

    cache = InMemoryTTLCache[str, dict](maxsize=100, ttl_seconds=999)
    service = QueryService(repository=repo, area_stats_cache=cache)

    r1 = service.get_area_stats(
        product="p1",
        year=2020,
        polygon_geojson=poly,
        only_forest=False,
        min_season_length=None,
        season_length_stat="mean",
    )
    r2 = service.get_area_stats(
        product="p1",
        year=2020,
        polygon_geojson=poly,
        only_forest=False,
        min_season_length=None,
        season_length_stat="mean",
    )

    assert r1 == r2 == {"n": 10, "mean_season_length": 123.0}
    assert repo.get_area_stats.call_count == 1


def test_area_stats_cache_key_includes_filters():
    repo = MagicMock()
    poly = {
        "type": "Polygon",
        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
    }
    repo.get_area_stats.return_value = {"n": 10}

    cache = InMemoryTTLCache[str, dict](maxsize=100, ttl_seconds=999)
    service = QueryService(repository=repo, area_stats_cache=cache)

    _ = service.get_area_stats(
        product="p1",
        year=2020,
        polygon_geojson=poly,
        only_forest=False,
        min_season_length=None,
        season_length_stat="mean",
    )

    _ = service.get_area_stats(
        product="p1",
        year=2020,
        polygon_geojson=poly,
        only_forest=True,  # changed filter => should miss cache
        min_season_length=None,
        season_length_stat="mean",
    )

    assert repo.get_area_stats.call_count == 2
