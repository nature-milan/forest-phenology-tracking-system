# Forest Phenology Tracking System (FPTS)

A Python system for computing **forest phenology metrics** (start/end of growing season, season length) from raster NDVI time series, designed with production-grade architecture and testability in mind.

Forest phenology metrics (e.g. green-up, senescence) are often computed in notebooks or ad-hoc scripts. This project explores how such computations can be modeled, tested, and exposed as a maintainable software system.

This project is designed as a **software engineering portfolio project** at the intersection of:
- geospatial data
- environmental science
- backend system design

------------------------------------------------------------------------

## Overview

The Forest Phenology Tracking System (FPTS) is a backend analytics
platform designed to compute and serve vegetation phenology metrics
(e.g., season length, SOS/EOS dates) at both point and polygon levels.

The system demonstrates: - Clean architecture separation (API → Service
→ Repository → SQL) - PostGIS-powered spatial querying -
Production-grade HTTP semantics (400 vs 404 correctness) - Integration
testing with real PostGIS - Query parameter validation and schema
contracts

------------------------------------------------------------------------

## Tech Stack

- Language: Python (3.11+/3.12)
- Environment & Packaging: Poetry
- Web Framework: FastAPI
- ASGI Server: Uvicorn
- Configuration: pydantic-settings
- Data Modeling:
        - Python dataclasses for domain models
        - Pydantic models for API schemas
- Database: Postgres + PostGIS for phenology metrics
- Logging: Standard library logging with centralized setup

------------------------------------------------------------------------

## Architecture

```
src/fpts/
├── api/ (FastAPI routers + schemas)
├── query/ (Application services)
├── storage/ (Repository interfaces + PostGIS implementation)
├── sql/queries/ (Runtime SQL)
├── config/ (Settings & configuration)
```

### Layers

API Layer - Request validation - Response schemas - HTTP error mapping

Application Layer - QueryService orchestrates read operations

Storage Layer - PhenologyRepository (abstract) -
PostGISPhenologyRepository (default production backend)

SQL Layer - All runtime SQL centralized in sql/queries/phenology.py

------------------------------------------------------------------------

## Implemented Endpoints

### 1. GET /phenology/point

Returns phenology metrics for a single location and year.

-   200 → Data found
-   404 → No data for that location/year

------------------------------------------------------------------------

### 2. GET /phenology/timeseries

Returns multi-year phenology metrics for a single location.

Parameters: - lat, lon - start_year, end_year - product

Behavior: - 400 → Invalid year range - 404 → No data found

------------------------------------------------------------------------

### 3. POST /phenology/area

Aggregates phenology metrics within a GeoJSON polygon for a given year.

Features: - Accepts Polygon or MultiPolygon - Geometry validation via
PostGIS (ST_IsValid, ST_IsEmpty) - Boundary-inclusive selection via
ST_Covers - Optional filters: - only_forest - min_season_length -
Supports statistics: - mean - median (via percentile_cont) - both

HTTP Semantics: - 400 → Invalid geometry - 404 → Valid geometry but no
intersecting data - 200 → Aggregated results

------------------------------------------------------------------------

## Getting started

Prerequisites
- Python 3.11+ (preferably 3.12).
- Poetry Installed.
- (Optional) Git & GitHub for version control.

------------------------------------------------------------------------

## Run Locally

This will give you the ability to test the /phenoloyg/point API endpoint on any one of repo, compute or auto modes

    a. Generate synthetic data
```bash
rm -rf data/raw/ndvi_synth

poetry run python -m fpts.scripts.make_synthetic_ndvi_stack
```

    b. Build and get API running (Only use -v tag if you want to clear the volume (databases and tables))
```bash
docker compose down -v --remove-orphans

docker compose up --build
```

    c. Call /phenology/point API endpoint from a new terminal tab
```bash
curl "http://localhost:8000/phenology/point?product=ndvi_synth&year=2020&lat=51.495&lon=-0.495&mode=repo"
```

    d. Tear down
run `ctrl + c` to stop the container
Then the following for clean up:
``` bash
rm -rf data/raw/ndvi_synth

docker compose down -v --remove-orphans
```

### Other relevant/ useful commands

- Check tables present in Docker container (Run in another terminal tab)
```bash
docker exec -it fpts-postgis psql -U postgres -d fpts -c "\dt"
```

### Functionality to be added

- Seed the data automatically on startup so that users can query without having to manually generate data before building app.
    - This will enable timeseries endpoint querying
- Add POST functionality so user can optioanlly add their own data.
- Logging (change logging back to structured logging for older messages)

------------------------------------------------------------------------

## Testing Strategy

-   Unit tests for service layer
-   Integration tests with real PostGIS
-   Synthetic spatial geometries seeded per test
-   Validation of:
    -   Mean/median correctness
    -   Filter behavior
    -   400 vs 404 behavior
    -   Enum validation (422)

Run tests:

- (UNIT): `poetry run pytest -q`
- (INTEGRATION ONLY):
    - For all integration tests, execute the following commands in order:
    - Start the test database:
        - `docker compose -f docker-compose.test.yml down -v --remove-orphans`
        - `docker compose -f docker-compose.test.yml up -d --build --force-recreate`
    - (OPTIONAL) Verify schema exists
        -  `docker compose -f docker-compose.test.yml exec -T postgis_test psql -U postgres -d fpts_test -c "\dt public.*"`
    - Run integration tests ONLY:
        - `poetry run pytest -m integration`
    - (OPTIONAL) Run BOTH integration and unit tests:
        - `poetry run pytest -m "integration or not integration"`
    - Tear down
        - `docker compose -f docker-compose.test.yml down -v --remove-orphans`

------------------------------------------------------------------------

## Most recent phase of project

Production Hardening:

-   Docker + docker-compose (API + PostGIS)
-   GitHub Actions CI (lint + tests + coverage)
-   Structured logging
-   Request logging middleware
-   Optional Prometheus metrics endpoint
-   Basic caching strategy

------------------------------------------------------------------------

## Future Polish

-   Architecture diagram
-   Engineering decisions document
-   Scaling discussion (tiling, batch jobs, async workers)
-   Optional minimal demo client (Notebook or small UI)
-   Deployment example (e.g., Fly.io / Render / AWS ECS)

------------------------------------------------------------------------

## Long-Term Extensions

-   Raster ingestion pipeline
-   Background workers for batch processing
-   Precomputed spatial tiles
-   GeoJSON FeatureCollection outputs
-   Time-series trend analysis (slope detection)
-   Vectorized polygon performance optimization

------------------------------------------------------------------------

## License

MIT (or update as appropriate)
