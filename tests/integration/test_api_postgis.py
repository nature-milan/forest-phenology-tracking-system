import pytest
import os
from datetime import date
from fastapi.testclient import TestClient

from fpts.api.main import create_app
from fpts.config.settings import Settings
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
