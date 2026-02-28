
import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_point_compute_in_bounds_returns_200(app_postgis) -> None:
    client = TestClient(app_postgis)
    resp = client.get(
        "/phenology/point",
        params={
            "product": "ndvi_synth",
            "year": 2020,
            "lat": 51.495,
            "lon": -0.495,
            "mode": "compute",
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["year"] == 2020
    assert body["location"]["lat"] == 51.495
    assert body["location"]["lon"] == -0.495


@pytest.mark.integration
def test_point_compute_out_of_bounds_returns_422(app_postgis) -> None:
    client = TestClient(app_postgis)
    resp = client.get(
        "/phenology/point",
        params={
            "product": "ndvi_synth",
            "year": 2020,
            "lat": 89.495,
            "lon": -1.495,
            "mode": "compute",
        },
    )
    assert resp.status_code == 422, resp.text
    body = resp.json()

    assert body["error"] == "out_of_coverage"
    assert body["requested"] == {"lat": 89.495, "lon": -1.495}

    cov = body["coverage"]
    assert cov["crs"] == "EPSG:4326"
    assert cov["lon_range"][0] < cov["lon_range"][1]
    assert cov["lat_range"][0] < cov["lat_range"][1]
    assert "tolerance_deg" in body
