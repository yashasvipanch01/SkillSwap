.PHONY: install migrate seed run test lint reset

install:
	pip install -r requirements-dev.txt

migrate:
	alembic upgrade head

seed:
	python -m app.seed

reset:
	python -m app.seed --reset

run:
	uvicorn app.main:app --reload

test:
	pytest

lint:
	ruff check .
