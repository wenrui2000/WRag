# Makefile for WRAG Application

.PHONY: all test build start stop restart clean setup rebuild logs

# Default target
all: build start

# Run all tests
test:
	@echo "Running all tests..."
	@cd backend && python -m pytest

# Build all services
build:
	@echo "Building Docker images..."
	@docker-compose build

# Start all services
start:
	@echo "Starting all services..."
	@docker-compose up -d

# Stop all services
stop:
	@echo "Stopping all services..."
	@docker-compose down

# Restart all services
restart:
	@echo "Restarting all services..."
	@docker-compose restart

# Clean Docker resources
clean:
	@echo "Cleaning Docker resources..."
	@docker-compose down -v
	@docker system prune -f

# Set up development environment
setup:
	@echo "Setting up development environment..."
	@python -m venv venv
	@echo "Run 'venv\\Scripts\\activate' to activate the virtual environment (Windows)"
	@echo "Run 'source venv/bin/activate' to activate the virtual environment (Linux/Mac)"

# Rebuild a specific service
# Usage: make rebuild SERVICE=indexing_service
rebuild:
	@if not defined SERVICE (echo "SERVICE is not defined. Usage: make rebuild SERVICE=indexing_service" & exit /b 1)
	@echo "Rebuilding service: $(SERVICE)..."
	@docker-compose build $(SERVICE)
	@docker-compose up -d --no-deps $(SERVICE)

# View logs for all or a specific service
# Usage: make logs [SERVICE=service_name]
logs:
	@if defined SERVICE (docker-compose logs -f $(SERVICE)) else (docker-compose logs -f) 