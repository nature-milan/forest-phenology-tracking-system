#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="docker-compose.test.yml"

cleanup() {
  docker compose -f "$COMPOSE_FILE" down -v --remove-orphans || true
}
trap cleanup EXIT

# Fresh start
docker compose -f "$COMPOSE_FILE" down -v --remove-orphans
docker compose -f "$COMPOSE_FILE" up -d --build --force-recreate

# Run tests (your selection)
poetry run pytest -m "integration or not integration"