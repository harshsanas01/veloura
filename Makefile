.PHONY: install dev dev-api dev-web test lint format migrate migration seed reseed-products validate-seed-images generate-embeddings build

VENV = apps/api/.venv
PY = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

install:
	python3.13 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e "./apps/api[dev]"
	cd apps/web && npm install

dev:
	@echo "Run 'make dev-api' and 'make dev-web' in separate terminals."

dev-api:
	$(VENV)/bin/uvicorn veloura_api.main:app --reload --port 8000

dev-web:
	cd apps/web && npm run dev

test:
	cd apps/api && .venv/bin/pytest tests/ -v

lint:
	cd apps/api && .venv/bin/ruff check src tests
	cd apps/api && .venv/bin/mypy src
	cd apps/web && npm run lint

format:
	cd apps/api && .venv/bin/ruff format src tests

migrate:
	cd apps/api && .venv/bin/alembic upgrade head

migration:
	cd apps/api && .venv/bin/alembic revision --autogenerate -m "$(m)"

seed:
	$(PY) scripts/seed_products.py

reseed-products:
	@echo "Safe reseed: refreshes seed-owned product images from the manifest;"
	@echo "users, auth data, carts, and orders are preserved. Deleting superseded"
	@echo "seed products requires 'python scripts/reseed_products.py --purge --confirm'."
	$(PY) scripts/reseed_products.py

validate-seed-images:
	$(PY) scripts/validate_seed_images.py

generate-embeddings:
	$(PY) scripts/generate_embeddings.py

build:
	cd apps/web && npm run build
