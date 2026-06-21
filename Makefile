COMPOSE_HOME = docker compose -f compose.home.yml
PYTHONPATH := $(shell pwd)/src
PYTHON := uv run

export UV_PROJECT_ENVIRONMENT

.PHONY: ci tests up_home up_home_d down run_home venv

ci:
	uv run ruff format
	uv run ruff check --fix

tests:
	PYTHONPATH=$(PYTHONPATH):. $(PYTHON) pytest --cov=src --cov-report=term-missing $(ARGS)

run_home:
	python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

up_home_d:
	$(COMPOSE_HOME) up --build -d

up_home:
	$(COMPOSE_HOME) up --build

down:
	$(COMPOSE_HOME) down -v

venv:
	uv python install 3.13
	uv sync --python 3.13
	@echo "✅ Environment is ready."

add:
	uv add $(pkg)

sync:
	uv sync
