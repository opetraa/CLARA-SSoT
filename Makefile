.PHONY: help install test lint format clean run docker-build docker-up dvc-repro

help:
	@echo "Available commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make test        - Run tests"
	@echo "  make lint        - Run linters"
	@echo "  make format      - Format code"
	@echo "  make clean       - Clean cache files"
	@echo "  make run         - Run API server"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-up   - Start services with docker-compose"
	@echo "  make dvc-repro   - Reproduce DVC pipeline"

install:
	poetry install

test:
	poetry run pytest tests/ -v --cov=src/clara_ssot

lint:
	poetry run pylint src/
	poetry run mypy src/

format:
	poetry run black src/ tests/
	poetry run isort src/ tests/

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".mypy_cache" -exec rm -r {} +

run:
	poetry run uvicorn src.clara_ssot.api.main:app --reload --host 0.0.0.0 --port 8000

docker-build:
	docker build -t clara-ssot:latest .

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

dvc-repro:
	dvc repro

dvc-push:
	dvc push

dvc-pull:
	dvc pull

dvc-status:
	dvc status
