from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import requests
from pystac_client import Client

try:
    import planetary_computer as pc
except Exception:
    pc = None

from fpts.config.settings import Settings


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """
    Returns the SHA-256 hash of a file's content as a hex string.
    """
    hash = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            hash.update(chunk)
    return hash.hexdigest()


def _doy_from_iso(dt: str) -> int:
    # dt is typically like "2020-01-01T00:00:00Z"
    d = datetime.fromisoformat(dt.replace("Z", "+00:00")).date()
    return int(d.strftime("%j"))


def download_to_path(
    url: str, out_path: Path, *, timeout_s: float = 60.0
) -> tuple[str, int]:
    """
    Download url -> out_path with atomic write.
    Returns (sha256, bytes).
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = out_path.with_suffix(out_path.suffix + ".partial")

    hash = hashlib.sha256()
    nbytes = 0

    with requests.get(url, stream=True, timeout=timeout_s) as r:
        r.raise_for_status()
        with tmp_path.open("wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if not chunk:
                    continue
                f.write(chunk)
                hash.update(chunk)
                nbytes += len(chunk)

    os.replace(tmp_path, out_path)  # atomic on same filesystem
    return (hash.hexdigest(), nbytes)


def read_plan(path: Path) -> Mod13Q1Plan:
    payload = json.loads(path.read_text())
    assets = [Mod13Q1AssetRef(**a) for a in payload["assets"]]
    return Mod13Q1Plan(
        collection=payload["collection"],
        year=int(payload["year"]),
        bbox=tuple(payload["bbox"]),
        assets=assets,
    )


def write_checksums(records: Iterable[DownloadRecord], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "files": [asdict(r) for r in records],
    }
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True))


@dataclass(frozen=True)
class Mod13Q1AssetRef:
    item_id: str
    dt: str  # ISO datetime string
    doy: int
    asset_key: str
    href: str  # signed href (Planetary Computer)


@dataclass(frozen=True)
class Mod13Q1Plan:
    collection: str
    year: int
    bbox: tuple[float, float, float, float]  # (min_lon, min_lat, max_lon, max_lat)
    assets: list[Mod13Q1AssetRef]


@dataclass(frozen=True)
class DownloadRecord:
    filename: str
    sha256: str
    bytes: int
    href: str
    item_id: str
    dt: str
    doy: int


class Mod13Q1IngestionService:

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def build_plan(
        self, *, year: int, bbox: tuple[float, float, float, float]
    ) -> Mod13Q1Plan:
        if pc is None:
            raise RuntimeError("planetary-computer package not available")

        catalog = Client.open(self._settings.pc_stac_url)
        dt_range = f"{year}-01-01/{year}-12-31"

        search = catalog.search(
            collections=[self._settings.mod13q1_collection],
            bbox=list(bbox),
            datetime=dt_range,
        )
        items = list(search.items())

        assets: list[Mod13Q1AssetRef] = []
        for item in items:
            signed = pc.sign(item).to_dict()  # sign each item to get SAS URLs
            props = signed.get("properties", {})
            dt = props.get("datetime")
            if not dt:
                # fallback if datetime missing
                dt = props.get("start_datetime") or props.get("end_datetime")
            if not dt:
                raise ValueError(
                    f"STAC item missing datetime fields: {signed.get('id')}"
                )

            # pick NDVI asset
            item_assets: dict[str, Any] = signed.get("assets", {})
            ndvi_key = self._settings.mod13q1_ndvi_asset_key

            if ndvi_key not in item_assets:
                # fail fast so we learn the exact asset key early
                raise ValueError(
                    "Expected 'ndvi' asset not found in item "
                    f"{signed.get('id')}; keys={list(item_assets)}"
                )

            href = item_assets[ndvi_key]["href"]
            assets.append(
                Mod13Q1AssetRef(
                    item_id=str(signed.get("id")),
                    dt=str(dt),
                    doy=_doy_from_iso(str(dt)),
                    asset_key=ndvi_key,
                    href=str(href),
                )
            )

        assets.sort(
            key=lambda a: (a.doy, a.item_id)
        )  # stable ordering for deterministic manifests
        return Mod13Q1Plan(
            collection=self._settings.mod13q1_collection,
            year=year,
            bbox=bbox,
            assets=assets,
        )

    def fetch_plan(
        self,
        plan: Mod13Q1Plan,
        *,
        data_dir: Path,
        product: str = "mod13q1",
        verify_existing: bool = True,
    ) -> list[DownloadRecord]:
        """
        Store as:
          {data_dir}/raw/{product}/{year}/doy_{doy:03d}.tif
          {data_dir}/raw/{product}/{year}/checksums.json
        """
        records: list[DownloadRecord] = []
        year_dir = data_dir / "raw" / product / str(plan.year)

        for asset in plan.assets:
            out = year_dir / f"doy_{asset.doy:03d}.tif"

            if out.exists() and verify_existing:
                digest = sha256_file(out)
                records.append(
                    DownloadRecord(
                        filename=str(out.name),
                        sha256=digest,
                        bytes=out.stat().st_size,
                        href=asset.href,
                        item_id=asset.item_id,
                        dt=asset.dt,
                        doy=asset.doy,
                    )
                )
                continue

            digest, nbytes = download_to_path(asset.href, out)
            records.append(
                DownloadRecord(
                    filename=str(out.name),
                    sha256=digest,
                    bytes=nbytes,
                    href=asset.href,
                    item_id=asset.item_id,
                    dt=asset.dt,
                    doy=asset.doy,
                )
            )

        write_checksums(records, year_dir / "checksums.json")
        return records

    def write_manifest(self, plan: Mod13Q1Plan, out_path: Path) -> None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        payload = asdict(plan)
        out_path.write_text(json.dumps(payload, indent=2, sort_keys=True))
