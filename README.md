# Forest Phenology Tracking System (FPTS)

A Python system for computing forest **forest phenology metrics** (start/end of growing season, season length) from raster NDVI time series, designed with production-grade architecture and testability in mind.

Forest phenology metrics (e.g. green-up, senescence) are often computed in notebooks or ad-hoc scripts. This project explores how such computations can be modeled, tested, and exposed as a maintainable software system.

This project is designed as a **software engineering portfolio project** at the intersection of:
- geospatial data
- environmental science
- backend system design

---

## Project Status

The system now supports **real raster-backed phenology computation** (using synthetic NDVI data for now), with:

- Clean layered architecture
- Deterministic, testable phenology algorithms
- Raster IO and NDVI time-series handling
- API endpoints backed by real computation
- Proper configuration, logging, and dependency injection

Real MODIS ingestion and persistence (PostGIS) are planned next.

---

## High-Level Architecture

```
HTTP API (FastAPI)
        ↓
Application Services
(QueryService / PhenologyComputationService)
        ↓
Processing Layer
(RasterService, NDVI stack, phenology algorithms)
        ↓
Storage Abstractions
(RasterRepository, PhenologyRepository)
        ↓
Domain Models
(Location, PhenologyMetric)
```

---

## API Overview

### Health Check

```
GET /health
```

Health check returns basic service info:
```json
{
  "status": "ok",
  "environment": "development",
  "log_level": "info"
}
```

### Point Phenology (Computed)

```
GET /phenology/point
```

Supports:
- repository-backed reads
- raster-backed on-the-fly computation

Point phenology returns metrics and metadata:
```python
(
year=metric.year,
location=LocationSchema(lat=metric.location.lat, lon=metric.location.lon),
sos_date=metric.sos_date,
eos_date=metric.eos_date,
season_length=metric.season_length,
is_forest=metric.is_forest
)
```

---

## Code Structure

```
src/fpts/
├── api/
├── domain/
├── processing/
├── storage/
├── query/
├── config/
├── utils/
├── scripts/
```

---

## Tech Stack

- Language: Python (3.11+/3.12)
- Environment & Packaging: Poetry
- Web Framework: FastAPI
- ASGI Server: Uvicorn
- Configuration: pydantic-settings
- Data Modeling:
        - Python dataclasses for domain models
        - Pydantic models for API schemas
- Logging: Standard library logging with centralized setup
- Planned additions:
        - Postgres + PostGIS for phenology metrics
        - Background processing pipelines for ingestion and phenology metric computation

---

## Getting started

Prerequisites
- Python 3.11+ (preferably 3.12).
- Poetry Installed.
- (Optional) Git & GitHub for version control.

---

## Running Locally

```bash
poetry install
poetry run python -m fpts.api
```

---

## Testing

Testing is split between unit and integration tests.
The integration tests use external services Docker and PostGIS.

1. To run unit tests only:
```bash
poetry run pytest
```

2. To run integration tests only:
- First we have to start the Docker container:
```bash
docker compose -f docker-compose.test.yml up -d
```
- Next run:
```bash
poetry run pytest -m integration
```
- Finally stop the Docker contianer after the test:
```bash
docker compose -f docker-compose.test.yml down -v
```

3. Same as above (2.) but replace the poetry command with:
```bash
poetry run pytest -m "integration or not integration"
```


---

## Roadmap

- MODIS NDVI ingestion
- PostGIS persistence
- Area-based phenology
- Docker & CI

---