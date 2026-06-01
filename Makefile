# Sovereign Grid Makefile
# Version: 31.0

.PHONY: help install dev test lint format docker-build docker-up docker-down deploy clean

help:
	@echo "Sovereign Grid Makefile"
	@echo ""
	@echo "Available commands:"
	@echo "  install      Install dependencies"
	@echo "  dev          Run development server"
	@echo "  test         Run tests"
	@echo "  lint         Run linters"
	@echo "  format       Format code"
	@echo "  docker-build Build Docker images"
	@echo "  docker-up    Start Docker Compose"
	@echo "  docker-down  Stop Docker Compose"
	@echo "  deploy       Deploy to production"
	@echo "  clean        Clean temporary files"

install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

dev:
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest tests/ -v --cov=backend --cov-report=term

test-integration:
	pytest tests/integration/ -v -m integration

test-all:
	pytest tests/ -v --cov=backend --cov-report=html

lint:
	flake8 backend/
	black --check backend/
	isort --check-only backend/
	mypy backend/

format:
	black backend/
	isort backend/

docker-build:
	docker build -f Dockerfile -t sovereign-grid/api:latest .
	docker build -f Dockerfile.worker -t sovereign-grid/worker:latest .

docker-up:
	docker-compose -f docker-compose.yml up -d

docker-down:
	docker-compose -f docker-compose.yml down

docker-logs:
	docker-compose -f docker-compose.yml logs -f

deploy:
	./scripts/deploy.sh production

deploy-staging:
	./scripts/deploy.sh staging

migrate:
	python scripts/migrate.py up

seed:
	python scripts/seed.py

backup:
	./scripts/backup.sh

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
