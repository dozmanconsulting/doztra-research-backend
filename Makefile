# Makefile for Doztra Auth Service

.PHONY: help setup venv install run test test-unit test-api lint format clean db-init db-migrate docker-build docker-run docker-stop

# Default target
help:
	@echo "Doztra Auth Service Makefile"
	@echo ""
	@echo "Usage:"
	@echo "  make setup         Create virtual environment and install dependencies"
	@echo "  make install       Install dependencies"
	@echo "  make run           Run the application"
	@echo "  make test          Run all tests"
	@echo "  make test-unit     Run unit tests"
	@echo "  make test-api      Run API tests"
	@echo "  make lint          Run linting"
	@echo "  make format        Format code"
	@echo "  make clean         Remove build artifacts and cache files"
	@echo "  make db-init       Initialize database with seed data"
	@echo "  make db-migrate    Run database migrations"
	@echo "  make docker-build  Build Docker image"
	@echo "  make docker-run    Run Docker container"
	@echo "  make docker-stop   Stop Docker container"

# Setup virtual environment and install dependencies
setup:
	@echo "Creating virtual environment..."
	python3 -m venv venv
	@echo "Installing dependencies..."
	. venv/bin/activate && pip install -r requirements.txt
	@echo "Setup complete. Activate the virtual environment with: source venv/bin/activate"

# Install dependencies
install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt

# Run the application
run:
	@echo "Starting the application..."
	python run.py --reload

# Run all tests
test:
	@echo "Running all tests..."
	python run_tests.py

# Run unit tests
test-unit:
	@echo "Running unit tests..."
	python -m pytest tests/unit -v

# Run API tests
test-api:
	@echo "Running API tests..."
	python tests/api_tests.py

# Run linting
lint:
	@echo "Running linting..."
	flake8 app tests
	mypy app tests

# Format code
format:
	@echo "Formatting code..."
	black app tests
	isort app tests

# Clean build artifacts and cache files
clean:
	@echo "Cleaning build artifacts and cache files..."
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .coverage
	rm -rf htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete

# Initialize database with seed data
db-init:
	@echo "Initializing database with seed data..."
	python init_db.py

# Run database migrations
db-migrate:
	@echo "Running database migrations..."
	alembic upgrade head

# Build Docker image
docker-build:
	@echo "Building Docker image..."
	docker-compose build

# Run Docker container
docker-run:
	@echo "Running Docker container..."
	docker-compose up -d

# Stop Docker container
docker-stop:
	@echo "Stopping Docker container..."
	docker-compose down
