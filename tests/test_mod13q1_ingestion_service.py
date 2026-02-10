from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import fpts.ingestion.mod13q1 as mod13q1
from fpts.config.settings import Settings
from fpts.ingestion.mod13q1 import Mod13Q1IngestionService

from fpts.config.settings import Settings

ndvi_key = Settings().mod13q1_ndvi_asset_key


class _FakeSearch:
    def __init__(self, items):
        self._items = items

    def items(self):
        return list(self._items)


class _FakeCatalog:
    def __init__(self, items):
        self._items = items

    def search(self, **kwargs):
        return _FakeSearch(self._items)


class _FakeSigned:
    def __init__(self, d):
        self._d = d

    def to_dict(self):
        return self._d


def _fake_sign(item):
    return _FakeSigned(item.to_dict())


def test_build_plan_extracts_ndvi_and_sorts_by_doy(monkeypatch):
    # Arrange: two items out of order
    fake_items = [
        SimpleNamespace(
            to_dict=lambda: {
                "id": "b",
                "properties": {"datetime": "2020-02-29T00:00:00Z"},
                "assets": {ndvi_key: {"href": "https://example.com/ndvi_b.tif"}},
            }
        ),
        SimpleNamespace(
            to_dict=lambda: {
                "id": "a",
                "properties": {"datetime": "2020-01-01T00:00:00Z"},
                "assets": {ndvi_key: {"href": "https://example.com/ndvi_a.tif"}},
            }
        ),
    ]

    monkeypatch.setattr(mod13q1, "pc", SimpleNamespace(sign=_fake_sign))
    monkeypatch.setattr(
        mod13q1.Client, "open", lambda *_args, **_kw: _FakeCatalog(fake_items)
    )

    svc = Mod13Q1IngestionService(settings=Settings())

    # Act
    plan = svc.build_plan(year=2020, bbox=(0.0, 0.0, 1.0, 1.0))

    # Assert: sorted by doy then id => Jan 1 (doy 1) before Feb 29 (doy 60)
    assert [a.item_id for a in plan.assets] == ["a", "b"]
    assert [a.doy for a in plan.assets] == [1, 60]
    assert [a.href for a in plan.assets] == [
        "https://example.com/ndvi_a.tif",
        "https://example.com/ndvi_b.tif",
    ]


def test_write_manifest_is_json(tmp_path: Path):
    svc = Mod13Q1IngestionService(settings=Settings())
    plan = svc.build_plan  # just to silence unused import, we won't call network

    # Minimal manifest write test (no plan building)
    from fpts.ingestion.mod13q1 import Mod13Q1Plan, Mod13Q1AssetRef

    pl = Mod13Q1Plan(
        collection="c",
        year=2020,
        bbox=(0.0, 0.0, 1.0, 1.0),
        assets=[
            Mod13Q1AssetRef(
                item_id="x",
                dt="2020-01-01T00:00:00Z",
                doy=1,
                asset_key="ndvi",
                href="h",
            )
        ],
    )

    out = tmp_path / "manifest.json"
    svc.write_manifest(pl, out)

    loaded = json.loads(out.read_text())
    assert loaded["year"] == 2020
    assert loaded["assets"][0]["item_id"] == "x"
