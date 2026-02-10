from __future__ import annotations

from typing import Iterable

import psycopg
from psycopg.rows import dict_row

from fpts.domain.models import PhenologyMetric
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
                return PhenologyMetric(**row)
