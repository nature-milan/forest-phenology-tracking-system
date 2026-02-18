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

```bash
poetry install
poetry run python -m fpts.api
```

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
    - `docker compose -f docker-compose.test.yml up -d`
    - Then run: `poetry run pytest -q -m integration`
    - `docker compose -f docker-compose.test.yml down -v`

- (UNIT AND INTEGRATION):
    - Follow Docker commands from above and replace the poetry command with the one below:
    - `poetry run pytest -q -m "integration or not integration"`

------------------------------------------------------------------------

## Next phase of project

Production Hardening:

-   Docker + docker-compose (API + PostGIS) ✅
-   GitHub Actions CI (lint + tests + coverage) ✅
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
