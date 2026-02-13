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


@pytest.mark.integration
def test_phenology_area_returns_aggregates_for_intersecting_points(app_postgis):
    repo = app_postgis.state.phenology_repo

    # Three points in 2020, only two inside our polygon
    p1 = Location(lat=52.50, lon=13.40)  # inside
    p2 = Location(lat=52.51, lon=13.41)  # inside
    p3 = Location(lat=52.60, lon=13.60)  # outside

    repo.upsert(
        product="test_product",
        metric=PhenologyMetric(
            year=2020,
            location=p1,
            sos_date=date(2020, 4, 10),
            eos_date=date(2020, 10, 10),
            season_length=183,
            is_forest=True,
        ),
    )
    repo.upsert(
        product="test_product",
        metric=PhenologyMetric(
            year=2020,
            location=p2,
            sos_date=date(2020, 4, 20),
            eos_date=date(2020, 10, 20),
            season_length=184,
            is_forest=False,
        ),
    )
    repo.upsert(
        product="test_product",
        metric=PhenologyMetric(
            year=2020,
            location=p3,
            sos_date=date(2020, 4, 1),
            eos_date=date(2020, 10, 1),
            season_length=183,
            is_forest=True,
        ),
    )

    # Small polygon around p1 & p2 (lon,lat order in GeoJSON)
    poly = {
        "type": "Polygon",
        "coordinates": [
            [
                [13.39, 52.49],
                [13.42, 52.49],
                [13.42, 52.52],
                [13.39, 52.52],
                [13.39, 52.49],
            ]
        ],
    }

    client = TestClient(app_postgis)
    resp = client.post(
        "/phenology/area",
        params={"product": "test_product", "year": 2020},
        json={"geometry": poly},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["product"] == "test_product"
    assert body["year"] == 2020
    assert body["n"] == 2
    assert abs(body["mean_season_length"] - ((183 + 184) / 2)) < 1e-9
    assert abs(body["forest_fraction"] - 0.5) < 1e-9


@pytest.mark.integration
def test_phenology_area_returns_404_when_no_matches(app_postgis):
    poly = {
        "type": "Polygon",
        "coordinates": [
            [
                [0.0, 0.0],
                [0.1, 0.0],
                [0.1, 0.1],
                [0.0, 0.1],
                [0.0, 0.0],
            ]
        ],
    }

    client = TestClient(app_postgis)
    resp = client.post(
        "/phenology/area",
        params={"product": "test_product", "year": 2020},
        json={"geometry": poly},
    )
    assert resp.status_code == 404
    assert (
        resp.json()["detail"]
        == "No phenology data found intersecting this polygon for the given product and year"
    )


@pytest.mark.integration
def test_area_returns_400_for_invalid_geometry(app_postgis):
    client = TestClient(app_postgis)

    invalid_poly = {"type": "Polygon", "coordinates": []}  # invalid ring

    resp = client.post(
        "/phenology/area",
        params={"product": "test_product", "year": 2020},
        json={"geometry": invalid_poly},
    )

    assert resp.status_code == 400
