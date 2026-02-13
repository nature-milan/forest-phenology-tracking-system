import pytest
from datetime import date
from fastapi.testclient import TestClient

from fpts.domain.models import Location, PhenologyMetric


@pytest.mark.integration
def test_phenology_point_returns_seeded_metric_postgis(app_postgis):
    # Seed explicitly into PostGIS via the repo (same test shape as memory)
    repo = app_postgis.state.phenology_repo
    loc = Location(lat=52.5, lon=13.4)
    repo.upsert(
        product="test_product",
        metric=PhenologyMetric(
            year=2020,
            location=loc,
            sos_date=date(2020, 4, 15),
            eos_date=date(2020, 10, 15),
            season_length=(date(2020, 10, 15) - date(2020, 4, 15)).days,
            is_forest=True,
        ),
    )

    client = TestClient(app_postgis)
    resp = client.get(
        "/phenology/point",
        params={
            "product": "test_product",
            "lat": 52.5,
            "lon": 13.4,
            "year": 2020,
        },
    )
    assert resp.status_code == 200


@pytest.mark.integration
def test_phenology_point_returns_404_for_missing_metric(app_postgis):
    client = TestClient(app_postgis)

    resp = client.get(
        "/phenology/point",
        params={
            "product": "test_product",
            "lat": 40.0,
            "lon": 10.0,
            "year": 2020,
            "mode": "repo",
        },
    )
    assert resp.status_code == 404
    assert (
        resp.json()["detail"]
        == f"No phenology data found for this combination of product, location and year"
    )


@pytest.mark.integration
def test_postgis_repo_timeseries_returns_sorted_rows(app_postgis):
    repo = app_postgis.state.phenology_repo
    loc = Location(lat=52.5, lon=13.4)

    repo.upsert(
        product="test_product",
        metric=PhenologyMetric(
            year=2021,
            location=loc,
            sos_date=date(2021, 4, 20),
            eos_date=date(2021, 10, 20),
            season_length=(date(2021, 10, 20) - date(2021, 4, 20)).days,
            is_forest=True,
        ),
    )
    repo.upsert(
        product="test_product",
        metric=PhenologyMetric(
            year=2019,
            location=loc,
            sos_date=date(2019, 4, 10),
            eos_date=date(2019, 10, 10),
            season_length=(date(2019, 10, 10) - date(2019, 4, 10)).days,
            is_forest=True,
        ),
    )

    qs = app_postgis.state.query_service
    out = qs.get_point_timeseries(
        product="test_product", location=loc, start_year=2018, end_year=2022
    )
    assert [metric.year for metric in out] == [2019, 2021]


@pytest.mark.integration
def test_phenology_timeseries_returns_seeded_metrics_postgis(app_postgis):
    repo = app_postgis.state.phenology_repo
    loc = Location(lat=52.5, lon=13.4)

    repo.upsert(
        product="test_product",
        metric=PhenologyMetric(
            year=2021,
            location=loc,
            sos_date=date(2021, 4, 20),
            eos_date=date(2021, 10, 20),
            season_length=(date(2021, 10, 20) - date(2021, 4, 20)).days,
            is_forest=True,
        ),
    )
    repo.upsert(
        product="test_product",
        metric=PhenologyMetric(
            year=2019,
            location=loc,
            sos_date=date(2019, 4, 10),
            eos_date=date(2019, 10, 10),
            season_length=(date(2019, 10, 10) - date(2019, 4, 10)).days,
            is_forest=True,
        ),
    )

    client = TestClient(app_postgis)
    resp = client.get(
        "/phenology/timeseries",
        params={
            "product": "test_product",
            "lat": 52.5,
            "lon": 13.4,
            "start_year": 2018,
            "end_year": 2022,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["product"] == "test_product"
    assert body["location"] == {"lat": 52.5, "lon": 13.4}
    assert body["start_year"] == 2018
    assert body["end_year"] == 2022
    assert [m["year"] for m in body["metrics"]] == [2019, 2021]


@pytest.mark.integration
def test_phenology_timeseries_returns_404_when_empty(app_postgis):
    client = TestClient(app_postgis)
    resp = client.get(
        "/phenology/timeseries",
        params={
            "product": "test_product",
            "lat": 52.5,
            "lon": 13.4,
            "start_year": 2018,
            "end_year": 2022,
        },
    )
    assert resp.status_code == 404
    assert (
        resp.json()["detail"]
        == "No phenology data found for this combination of product, location and year range"
    )
