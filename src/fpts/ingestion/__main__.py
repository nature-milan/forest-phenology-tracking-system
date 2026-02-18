from __future__ import annotations

import argparse
from pathlib import Path

from fpts.config.settings import Settings
from fpts.ingestion.mod13q1 import Mod13Q1IngestionService, read_plan


def _parse_bbox(string: str) -> tuple[float, float, float, float]:
    parts = [part.strip() for part in string.split(",")]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError(
            "bbox must be 'min_lon, min_lat, max_lon, max_lat'"
        )
    return (float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3]))


def main() -> None:
    p = argparse.ArgumentParser(prog="python -m fpts.ingestion")
    sub = p.add_subparsers(dest="cmd", required=True)

    plan = sub.add_parser("plan", help="Create a manifest for MOD13Q1 NDVI assets")
    plan.add_argument("--year", type=int, required=True)
    plan.add_argument("--bbox", type=_parse_bbox, required=True)
    plan.add_argument("--data-dir", type=Path, default=Path("data"))

    fetch = sub.add_parser("fetch", help="Download rasters from a manifest")
    fetch.add_argument("--manifest", type=Path, required=True)
    fetch.add_argument("--data-dir", type=Path, default=Path("data"))
    fetch.add_argument("--product", type=str, default="mod13q1")
    fetch.add_argument("--no-verify-existing", action="store_true")

    args = p.parse_args()

    settings = Settings()
    svc = Mod13Q1IngestionService(settings=settings)

    if args.cmd == "plan":
        plan = svc.build_plan(year=args.year, bbox=args.bbox)
        out = args.data_dir / "raw" / "mod13q1" / str(args.year) / "manifest.json"
        svc.write_manifest(plan, out)
        print(f"Wrote manifest: {out} ({len(plan.assets)} items)")

    if args.cmd == "fetch":
        plan_path: Path = args.manifest
        plan = read_plan(plan_path)
        records = svc.fetch_plan(
            plan,
            data_dir=args.data_dir,
            product=args.product,
            verify_existing=not args.no_verify_existing,
        )
        print(
            f"Fetched {len(records)} files into "
            f"{args.data_dir / 'raw' / args.product / str(plan.year)}"
        )


if __name__ == "__main__":
    main()
