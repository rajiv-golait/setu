# SETU dev workflow. Run from repo root: `make -C infra <target>` or `cd infra && make <target>`.
COMPOSE = docker compose -f docker-compose.yml
API_DIR = ../apps/api

.PHONY: dev seed gen-client test migrate down logs

## Start the full stack (db, redis, api hot-reload). Mock providers -> no GPU.
dev:
	$(COMPOSE) up --build

## Load the demo patient (claims + truth + brief + summary + share).
seed:
	$(COMPOSE) exec api python -m app.seed.demo_patient

## Export openapi.json -> packages/contracts/ (for the frontend client).
gen-client:
	$(COMPOSE) exec api python -m scripts.export_openapi

## Backend tests (reducer, validation, brief flags, pipeline smoke, contract).
test:
	cd $(API_DIR) && pytest -q

## Apply DB migrations.
migrate:
	$(COMPOSE) exec api alembic upgrade head

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f api
