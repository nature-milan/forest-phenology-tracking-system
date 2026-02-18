from datetime import date

from fastapi.testclient import TestClient

from fpts.domain.models import Location, PhenologyMetric


def test_phenology_point_returns_seeded_metric(app_memory):
    # Seed explicitly into the app's repo
    repo = app_memory.state.phenology_repo
    loc = Location(lat=52.5, lon=13.4)
    repo.add_metric(
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

    client = TestClient(app_memory)
    resp = client.get(
        "/phenology/point",
        params={
            "product": "test_product",
            "lat": 52.5,
            "lon": 13.4,
            "year": 2020,
            "mode": "repo",
        },
    )
    assert resp.status_code == 200

    data = resp.json()
    assert data["year"] == 2020
    assert data["location"]["lat"] == 52.5
    assert data["location"]["lon"] == 13.4
    assert data["is_forest"] is True
    assert data["sos_date"] == "2020-04-15"
    assert data["eos_date"] == "2020-10-15"
    assert data["season_length"] == 183


def test_phenology_point_returns_404_for_missing_metric(
    app_memory, test_product="test_product", lat=40.0, lon=10.0, year=2020
):
    client = TestClient(app_memory)
    resp = client.get(
        "/phenology/point",
        params={
            "product": test_product,
            "lat": lat,
            "lon": lon,
            "year": year,
            "mode": "repo",
        },
    )

    detail = resp.json()["detail"]

    assert resp.status_code == 404
    assert "No phenology data found for product" in detail
    assert f"{test_product}" in detail
    assert f"{Location(lat=lat, lon=lon)}" in detail
    assert f"{year}" in detail


def test_phenology_point_compute_mode_returns_200(app_memory):
    client = TestClient(app_memory)
    resp = client.get(
        "/phenology/point",
        params={
            "product": "ndvi_synth",
            "lat": 40.0,
            "lon": 10.0,
            "year": 2020,
            "mode": "compute",
        },
    )

    assert resp.status_code == 200


def test_phenology_point_auto_mode_returns_200(app_memory):
    client = TestClient(app_memory)
    resp = client.get(
        "/phenology/point",
        params={
            "product": "ndvi_synth",
            "lat": 40.0,
            "lon": 10.0,
            "year": 2020,
            "mode": "auto",
        },
    )

    assert resp.status_code == 200
