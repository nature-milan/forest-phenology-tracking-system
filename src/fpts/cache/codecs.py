from __future__ import annotations

from datetime import date
from typing import Any

from fpts.domain.models import Location, PhenologyMetric


def encode_metric(m: PhenologyMetric) -> dict[str, Any]:
    return {
        "year": m.year,
        "location": {"lat": m.location.lat, "lon": m.location.lon},
        "sos_date": m.sos_date.isoformat() if m.sos_date else None,
        "eos_date": m.eos_date.isoformat() if m.eos_date else None,
        "season_length": m.season_length,
        "is_forest": m.is_forest,
    }


def decode_metric(d: dict[str, Any]) -> PhenologyMetric:
    return PhenologyMetric(
        year=int(d["year"]),
        location=Location(
            lat=float(d["location"]["lat"]), lon=float(d["location"]["lon"])
        ),
        sos_date=date.fromisoformat(d["sos_date"]) if d.get("sos_date") else None,
        eos_date=date.fromisoformat(d["eos_date"]) if d.get("eos_date") else None,
        season_length=d.get("season_length"),
        is_forest=bool(d["is_forest"]),
    )


def encode_metric_list(items: list[PhenologyMetric]) -> list[dict[str, Any]]:
    return [encode_metric(m) for m in items]


def decode_metric_list(items: list[dict[str, Any]]) -> list[PhenologyMetric]:
    return [decode_metric(d) for d in items]
