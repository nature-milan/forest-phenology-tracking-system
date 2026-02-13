from __future__ import annotations

from typing import Iterable

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Json

from fpts.domain.models import Location, PhenologyMetric
from fpts.storage.phenology_repository import PhenologyRepository


class PostGISPhenologyRepository(PhenologyRepository):
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def _connect(self):
        return psycopg.connect(self._dsn, row_factory=dict_row)

    def upsert(self, *, product: str, metric: PhenologyMetric) -> None:
        self.upsert_many(product=product, metrics=[metric])

    def upsert_many(self, *, product: str, metrics: Iterable[PhenologyMetric]) -> None:
        sql = """
        INSERT INTO phenology_metrics (
            product, year, lon, lat, geom,
            sos_date, eos_date, season_length, is_forest
        )
        VALUES (
            %(product)s, %(year)s, %(lon)s, %(lat)s,
            ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326),
            %(sos_date)s, %(eos_date)s, %(season_length)s, %(is_forest)s
        )
        ON CONFLICT (product, year, lon, lat)
        DO UPDATE SET
            sos_date = EXCLUDED.sos_date,
            eos_date = EXCLUDED.eos_date,
            season_length = EXCLUDED.season_length,
            is_forest = EXCLUDED.is_forest;
        """

        with self._connect() as conn:
            with conn.cursor() as cur:
                for metric in metrics:
                    cur.execute(
                        sql,
                        {
                            "product": product,
                            "year": metric.year,
                            "lon": metric.location.lon,
                            "lat": metric.location.lat,
                            "sos_date": metric.sos_date,
                            "eos_date": metric.eos_date,
                            "season_length": metric.season_length,
                            "is_forest": metric.is_forest,
                        },
                    )

    def get_metric_for_location(
        self,
        *,
        product: str,
        location: Location,
        year: int,
    ) -> PhenologyMetric | None:
        sql = """
        SELECT
            year,
            lat,
            lon,
            sos_date,
            eos_date,
            season_length,
            is_forest
        FROM phenology_metrics
        WHERE
            product = %(product)s
            AND year = %(year)s
            AND lat = %(lat)s
            AND lon = %(lon)s
        """

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql,
                    {
                        "year": year,
                        "product": product,
                        "lon": location.lon,
                        "lat": location.lat,
                    },
                )
                row = cur.fetchone()
                if row is None:
                    return None

                return PhenologyMetric(
                    year=int(row["year"]),
                    location=Location(lat=float(row["lat"]), lon=float(row["lon"])),
                    sos_date=row["sos_date"],
                    eos_date=row["eos_date"],
                    season_length=row["season_length"],
                    is_forest=row["is_forest"],
                )

    def get_timeseries_for_location(
        self,
        *,
        product: str,
        location: Location,
        start_year: int,
        end_year: int,
    ) -> list[PhenologyMetric]:
        if end_year < start_year:
            return []

        sql = """
        SELECT
            year,
            lat,
            lon,
            sos_date,
            eos_date,
            season_length,
            is_forest
        FROM phenology_metrics
        WHERE
            product = %(product)s
            AND lat = %(lat)s
            AND lon = %(lon)s
            AND year BETWEEN %(start_year)s AND %(end_year)s
        ORDER BY year ASC
        """

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql,
                    {
                        "product": product,
                        "lat": location.lat,
                        "lon": location.lon,
                        "start_year": start_year,
                        "end_year": end_year,
                    },
                )
                rows = cur.fetchall() or []

        out: list[PhenologyMetric] = []
        for row in rows:
            out.append(
                PhenologyMetric(
                    year=int(row["year"]),
                    location=Location(lat=float(row["lat"]), lon=float(row["lon"])),
                    sos_date=row["sos_date"],
                    eos_date=row["eos_date"],
                    season_length=row["season_length"],
                    is_forest=row["is_forest"],
                )
            )
        return out

    def get_area_stats(
        self,
        *,
        product: str,
        year: int,
        polygon_geojson: dict,
    ) -> dict | None:
        sql = """
        WITH poly AS (
            SELECT ST_SetSRID(ST_GeomFromGeoJSON(%(poly)s), 4326) AS g
        ),
        flags AS (
            SELECT
                g,
                (g IS NOT NULL) AS not_null,
                (g IS NOT NULL AND NOT ST_IsEmpty(g)) AS not_empty,
                (g IS NOT NULL AND ST_IsValid(g)) AS is_valid,
                (g IS NOT NULL AND NOT ST_IsEmpty(g) AND ST_IsValid(g)) AS ok
            FROM poly
        )
        SELECT
            f.ok AS ok,
            COUNT(m.*)::int AS n,
            AVG(m.season_length)::float AS mean_season_length,
            AVG(CASE WHEN m.is_forest THEN 1 ELSE 0 END)::float AS forest_fraction
        FROM flags f
        LEFT JOIN phenology_metrics m
            ON f.ok
            AND m.product = %(product)s
            AND m.year = %(year)s
            AND ST_Covers(f.g, m.geom)
        GROUP BY f.ok
        """

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql,
                    {
                        "product": product,
                        "year": year,
                        "poly": Json(polygon_geojson),
                    },
                )
                row = cur.fetchone()

        # row should always exist because flags yields 1 row
        if row is None or row["ok"] is not True:
            raise ValueError("Invalid GeoJSON geometry")

        if row["n"] == 0:
            return None

        return {
            "n": int(row["n"]),
            "mean_season_length": row["mean_season_length"],
            "forest_fraction": row["forest_fraction"],
        }
