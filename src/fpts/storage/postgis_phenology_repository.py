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

    def upsert(self, metric: PhenologyMetric) -> None:
        self.upsert_many([metric])

    def upsert_many(self, metrics: Iterable[PhenologyMetric]) -> None:
        sql = """
        INSERT INTO phenology_metrics (
            product, year, geom,
            greenup_doy, maturity_doy, senescence_doy,
            ndvi_max, ndvi_mean
        )
        VALUES (
            %(product)s,
            %(year)s,
            ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326),
            %(greenup_doy)s, %(maturity_doy)s, %(senescence_doy)s,
            %(ndvi_max)s, %(ndvi_mean)s
        )
        ON CONFLICT (product, year, geom)
        DO UPDATE SET
            greenup_doy = EXCLUDED.greenup_doy,
            maturity_doy = EXCLUDED.maturity_doy,
            senescence_doy = EXCLUDED.senescence_doy,
            ndvi_max = EXCLUDED.ndvi_max,
            ndvi_mean = EXCLUDED.ndvi_mean;
        """

        with self._connect() as conn:
            with conn.cursor() as cur:
                for m in metrics:
                    cur.execute(
                        sql,
                        {
                            "product": m.product,
                            "year": m.year,
                            "lon": m.lon,
                            "lat": m.lat,
                            "greenup_doy": m.greenup_doy,
                            "maturity_doy": m.maturity_doy,
                            "senescence_doy": m.senescence_doy,
                            "ndvi_max": m.ndvi_max,
                            "ndvi_mean": m.ndvi_mean,
                        },
                    )

    def get_point(
        self,
        *,
        lon: float,
        lat: float,
        year: int,
        product: str,
    ) -> PhenologyMetric | None:
        sql = """
        SELECT
            product, year,
            ST_X(geom) AS lon,
            ST_Y(geom) AS lat,
            greenup_doy, maturity_doy, senescence_doy,
            ndvi_max, ndvi_mean
        FROM phenology_metrics
        WHERE
            product = %(product)s
            AND year = %(year)s
            AND ST_Equals(
                geom,
                ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326)
            )
        """

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql, {"lon": lon, "lat": lat, "year": year, "product": product}
                )
                row = cur.fetchone()
                if row is None:
                    return None
                return PhenologyMetric(**row)
