from __future__ import annotations

import argparse
import sys

from fpts.config.settings import Settings
from fpts.processing.batch.process_year import GridSpec, process_year_to_db


def main() -> None:
    p = argparse.ArgumentParser(prog="python -m fpts.processing.batch")
    sub = p.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser(
        "process-year", help="Compute phenology for a grid and upsert into PostGIS"
    )
    run.add_argument("--product", type=str, required=True)
    run.add_argument("--year", type=int, required=True)
    run.add_argument(
        "--bbox", type=str, required=True, help="min_lon,min_lat,max_lon,max_lat"
    )
    run.add_argument("--step-deg", type=float, default=0.02)

    args = p.parse_args()
    settings = Settings()

    min_lon, min_lat, max_lon, max_lat = [
        float(x.strip()) for x in args.bbox.split(",")
    ]
    grid = GridSpec(
        min_lon=min_lon,
        min_lat=min_lat,
        max_lon=max_lon,
        max_lat=max_lat,
        step_deg=args.step_deg,
    )

    n = process_year_to_db(
        settings=settings, product=args.product, year=args.year, grid=grid
    )
    print(
        f"Upserted {n} metrics into PostGIS for product={args.product} year={args.year}"
    )


if __name__ == "__main__":
    sys.exit(0)
    main()
