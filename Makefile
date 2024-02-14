PYTHON_SOURCES = publication_admin tests migrations

run:  ## [Local development] Run document publication admin API over HTTP on port 8000
	uvicorn publication_admin.main:app --host 0.0.0.0 --port 8000 --reload

test:
	pytest

coverage:
	pytest --cov=publication_admin --cov-report=html
	open htmlcov/index.html

lint:  ## [Local development] Run code quality checks (formatting, imports, lint, types, etc)
	ruff check ${PYTHON_SOURCES}

format:  ## [Local development] Auto-format python code
	ruff format ${PYTHON_SOURCES} && ruff check --fix ${PYTHON_SOURCES}

make-migrations:
	alembic revision --autogenerate --rev-id $(ls migrations/versions/*.py | wc -l)

migrate:
	alembic upgrade head


.PHONY: help

help: # Run `make help` to get help on the make commands
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
