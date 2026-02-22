from __future__ import annotations

import hashlib
import json

from fpts.domain.models import Location


def _stable_json_hash(obj: dict) -> str:
    """
    Stable hash for GeoJSON / params dictionaries.
    Ensures identical polygons with different key order map to the same cache key.
    """
    s = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def area_stats_cache_key(
    *,
    product: str,
    year: int,
    polygon_geojson: dict,
    only_forest: bool,
    min_season_length: int | None,
    season_length_stat: str,
) -> str:
    poly_h = _stable_json_hash(polygon_geojson)
    return (
        "phenology:area_stats:"
        f"{product}:{year}:{poly_h}:only_forest={only_forest}:"
        f"min_season_length={min_season_length}:season_length_stat={season_length_stat}"
    )


def timeseries_cache_key(
    *,
    product: str,
    location: Location,
    start_year: int,
    end_year: int,
) -> str:
    lat = round(location.lat, 6)
    lon = round(location.lon, 6)
    return f"phenology:timeseries:{product}:{lat}:{lon}:{start_year}:{end_year}"


def point_metric_cache_key(
    *,
    source: str,  # "repo" or "compute"
    product: str,
    year: int,
    location: Location,
    threshold_frac: float | None,
) -> str:
    """
    Normalize floats so equivalent requests map to the same key.

    - lat/lon rounded to 6dp: ~0.11m precision at equator (more than enough here)
    - threshold rounded to 3dp
    """
    lat = round(location.lat, 6)
    lon = round(location.lon, 6)
    thr = None if threshold_frac is None else round(threshold_frac, 3)
    return f"phenology:point:{source}:{product}:{year}:{lat}:{lon}:{thr}"
