from datetime import date

from fastapi.testclient import TestClient

from fpts.api.main import create_app
from fpts.domain.models import Location, PhenologyMetric


def test_phenology_point_returns_seeded_metric():
    app = create_app()

    # Seed explicitly into the app's repo
    repo = app.state.phenology_repo
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

    client = TestClient(app)
    resp = client.get(
        "/phenology/point",
        params={"product": "test_product", "lat": 52.5, "lon": 13.4, "year": 2020},
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
    app = create_app()
    client = TestClient(app)

    resp = client.get(
        "/phenology/point", params={"lat": 40.0, "lon": 10.0, "year": 2020}
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "No phenology data found for this location/year"
