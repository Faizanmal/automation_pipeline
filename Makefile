.PHONY: help install test lint format type-check run report dashboard clean docker-build docker-run

help:
	@echo "Automation Pipeline - Development Commands"
	@echo "==========================================="
	@echo ""
	@echo "Development:"
	@echo "  make install       - Install dependencies"
	@echo "  make test          - Run tests with coverage"
	@echo "  make lint          - Run linting checks"
	@echo "  make format        - Format code with black"
	@echo "  make type-check    - Run type checking with mypy"
	@echo "  make validate      - Validate configuration"
	@echo ""
	@echo "Pipeline:"
	@echo "  make run           - Run the pipeline"
	@echo "  make config        - Generate example config"
	@echo "  make report        - Generate coverage report"
	@echo "  make dashboard     - Start web dashboard"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make docker-run    - Run pipeline in Docker"
	@echo "  make docker-shell  - Open shell in Docker container"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean         - Remove generated files"
	@echo "  make clean-all     - Remove all build artifacts"

install:
	pip install -r requirements.txt

test:
	pytest tests/ -v --cov=pipeline --cov-report=html
	@echo "Coverage report: htmlcov/index.html"

test-quick:
	pytest tests/ -v

lint:
	flake8 pipeline/ main.py tests/

format:
	black pipeline/ main.py tests/ *.py

type-check:
	mypy pipeline/ main.py --ignore-missing-imports

validate:
	python validate.py

run:
	python main.py run --log-level INFO

run-debug:
	python main.py run --log-level DEBUG

config:
	python main.py example-config

report:
	python main.py report

dashboard:
	python dashboard.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete
	rm -rf .pytest_cache/

clean-all: clean
	rm -rf htmlcov/
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/

docker-build:
	docker build -t automation-pipeline:latest .

docker-run:
	docker-compose up

docker-shell:
	docker-compose run --rm pipeline /bin/bash

setup:
	python setup_project.py

.DEFAULT_GOAL := help
