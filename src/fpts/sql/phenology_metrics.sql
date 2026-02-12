CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS phenology_metrics (
    id SERIAL PRIMARY KEY,

    product TEXT NOT NULL,
    year INTEGER NOT NULL,

    -- store lon/lat explicitly for exact point lookups
    lon DOUBLE PRECISION NOT NULL,
    lat DOUBLE PRECISION NOT NULL,

    -- spatial column for PostGIS queries
    geom GEOMETRY(Point, 4326) NOT NULL,

    sos_date DATE,
    eos_date DATE,
    season_length INTEGER,
    is_forest BOOLEAN NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (product, year, lon, lat)
);

CREATE INDEX IF NOT EXISTS idx_phenology_metrics_geom
ON phenology_metrics
USING GIST (geom);

CREATE INDEX IF NOT EXISTS idx_phenology_metrics_product_year
ON phenology_metrics (product, year);
