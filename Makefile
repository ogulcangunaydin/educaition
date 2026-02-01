.PHONY: help install lint lint-fix format format-check test run seed clean

help:
	@echo "Available commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make lint         - Run linter (check only)"
	@echo "  make lint-fix     - Run linter and fix issues"
	@echo "  make format       - Format code"
	@echo "  make format-check - Check code formatting"
	@echo "  make test         - Run tests"
	@echo "  make run          - Run development server"
	@echo "  make seed         - Seed the database"
	@echo "  make clean        - Clean cache files"

install:
	pip install -r requirements.txt
	pip install ruff

lint:
	ruff check app/

lint-fix:
	ruff check app/ --fix

format:
	ruff format app/

format-check:
	ruff format app/ --check

check: lint format-check

fix: lint-fix format

test:
	pytest

run:
	uvicorn app.main:app --reload --port 3000

seed:
	python -m app.seeds.seed

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
