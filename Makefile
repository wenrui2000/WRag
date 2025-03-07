# Makefile for Haystack RAG App

.PHONY: test test-unit build build-base build-services start stop restart clean rebuild-service rebuild-after-fix

# Run all tests
test:
	@scripts/run_tests.bat

# Run unit tests only
test-unit:
	@scripts/run_tests.bat

# Build all images
build: test-unit build-base build-services

# Build base image
build-base:
	@scripts/build_base.bat

# Build service images
build-services:
	@scripts/build_services.bat

# Start all services
start:
	@scripts/start_services.bat

# Stop all services
stop:
	@scripts/stop_services.bat

# Restart all services
restart: stop clean build start

# Clean Docker resources
clean:
	@scripts/clean.bat

# Rebuild a specific service
# Usage: make rebuild-service SERVICE=indexing_service
rebuild-service:
	@if not defined SERVICE (echo SERVICE is not defined. Usage: make rebuild-service SERVICE=indexing_service & exit /b 1)
	@scripts/rebuild_service.bat $(SERVICE)

# Rebuild services after pipeline loader fix
rebuild-after-fix:
	@scripts/rebuild_after_fix.bat 