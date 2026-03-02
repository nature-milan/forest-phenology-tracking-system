from __future__ import annotations

import argparse
import csv
import hashlib
import math
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path


@dataclass(frozen=True)
class Bounds:
    lon_min: float
    lon_max: float
    lat_min: float
    lat_max: float


def _stable_u01(key: str) -> float:
    """
    Deterministic float in [0,1) from a string key (stable across runs/machines).
    """
    h = hashlib.sha256(key.encode("utf-8")).digest()
    # take 8 bytes -> int -> scale
    n = int.from_bytes(h[:8], "big")
    return (n % (10**12)) / float(10**12)


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _is_forest(lat: float, lon: float) -> bool:
    """
    Synthetic 'forest likelihood' field with spatial coherence.
    Tuned to give a mix of True/False across the region.
    """
    # Smooth spatial signal
    signal = (
        0.55 + 0.25 * math.sin(math.radians(lat * 3.0)) + 0.20 * math.cos(math.radians(lon * 2.0))
    )
    # Small deterministic "noise"
    noise = (_stable_u01(f"forest|{lat:.5f}|{lon:.5f}") - 0.5) * 0.20
    p = _clamp(signal + noise, 0.05, 0.95)
    u = _stable_u01(f"forest_draw|{lat:.5f}|{lon:.5f}")
    return u < p


def _phenology_dates(year: int, lat: float, lon: float, is_forest: bool) -> tuple[date, date, int]:
    """
    Generate plausible SOS/EOS with:
    - latitude effect (higher lat -> later SOS, earlier EOS)
    - a bit of longitude effect
    - forest tends to have slightly longer seasons
    - year-to-year shift
    """
    # Base day-of-year anchors
    base_sos = 85  # ~ late March
    base_eos = 295  # ~ late Oct

    lat_effect = (lat / 90.0) * 35.0  # up to ~35 days shift
    lon_effect = math.sin(math.radians(lon * 2.0)) * 6.0  # +/- ~6 days

    forest_bonus = -4.0 if is_forest else 2.0  # forests green-up a bit earlier
    forest_eos_bonus = 6.0 if is_forest else -3.0  # forests senesce later

    year_u = _stable_u01(f"yearshift|{year}")
    year_shift = (year_u - 0.5) * 10.0  # +/- 5 days

    sos_doy = int(round(base_sos + lat_effect + lon_effect + forest_bonus + year_shift))
    eos_doy = int(round(base_eos - lat_effect + lon_effect + forest_eos_bonus + year_shift))

    # keep sane
    sos_doy = int(_clamp(sos_doy, 30, 180))
    eos_doy = int(_clamp(eos_doy, 200, 360))

    # Ensure eos after sos by at least 30 days
    if eos_doy <= sos_doy + 30:
        eos_doy = sos_doy + 30

    sos = date(year, 1, 1) + timedelta(days=sos_doy - 1)
    eos = date(year, 1, 1) + timedelta(days=eos_doy - 1)
    season_len = (eos - sos).days

    return sos, eos, season_len


def generate_points(bounds: Bounds, step_deg: float) -> list[tuple[float, float]]:
    lons = []
    x = bounds.lon_min
    while x <= bounds.lon_max + 1e-12:
        lons.append(round(x, 6))
        x += step_deg

    lats = []
    y = bounds.lat_min
    while y <= bounds.lat_max + 1e-12:
        lats.append(round(y, 6))
        y += step_deg

    return [(lon, lat) for lat in lats for lon in lons]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="data/seed/phenology_metrics_seed.csv")
    p.add_argument("--product", default="ndvi_synth")
    p.add_argument("--year-from", type=int, default=2018)
    p.add_argument("--year-to", type=int, default=2022)
    p.add_argument("--lon-min", type=float, default=-2.0)
    p.add_argument("--lon-max", type=float, default=2.0)
    p.add_argument("--lat-min", type=float, default=88.0)
    p.add_argument("--lat-max", type=float, default=90.0)
    p.add_argument("--step-deg", type=float, default=0.5)
    args = p.parse_args()

    bounds = Bounds(args.lon_min, args.lon_max, args.lat_min, args.lat_max)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    points = generate_points(bounds, args.step_deg)
    years = list(range(args.year_from, args.year_to + 1))

    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "product",
                "year",
                "lon",
                "lat",
                "sos_date",
                "eos_date",
                "season_length",
                "is_forest",
            ],
        )
        w.writeheader()

        for year in years:
            for lon, lat in points:
                forest = _is_forest(lat=lat, lon=lon)
                sos, eos, season_len = _phenology_dates(
                    year=year, lat=lat, lon=lon, is_forest=forest
                )

                w.writerow(
                    {
                        "product": args.product,
                        "year": year,
                        "lon": lon,
                        "lat": lat,
                        "sos_date": sos.isoformat(),
                        "eos_date": eos.isoformat(),
                        "season_length": season_len,
                        "is_forest": "true" if forest else "false",
                    }
                )

    n_rows = len(points) * len(years)
    print(f"Wrote {n_rows} rows to {out_path} for product={args.product}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
