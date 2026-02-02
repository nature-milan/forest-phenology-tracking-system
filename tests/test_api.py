from fastapi.testclient import TestClient

from fpts.api.main import app


client = TestClient(app)


def test_phenology_point_returns_seeded_metric():
    # This matches the seeded metric in fpts/api/dependencies.py
    resp = client.get(
        "/phenology/point", params={"lat": 52.5, "lon": 13.4, "year": 2020}
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


def test_phenology_point_returns_404_for_missing_metric():
    resp = client.get(
        "/phenology/point", params={"lat": 40.0, "lon": 10.0, "year": 2020}
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "No phenology data found for this location/year."
