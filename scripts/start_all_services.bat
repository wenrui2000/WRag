@echo off
echo ====================================================================
echo Starting All Services (Backend, Frontend, and Nginx)
echo ====================================================================

REM Stop any running services first
echo Stopping any existing services...
docker-compose down
if %ERRORLEVEL% NEQ 0 (
    echo Warning: Error stopping services. Some services might not be running.
) else (
    echo All services stopped successfully.
)

REM Start the infrastructure services first
echo Starting infrastructure services (Elasticsearch, Qdrant, Ollama)...
docker-compose up -d elasticsearch qdrant ollama
if %ERRORLEVEL% NEQ 0 (
    echo Error starting infrastructure services. Please check docker-compose logs.
    exit /b 1
)

REM Wait for infrastructure to be ready
echo Waiting for infrastructure services to be ready...
timeout /t 10 /nobreak

REM Start the backend services
echo Starting backend services (Indexing Service, Query Service)...
docker-compose up -d indexing_service query_service
if %ERRORLEVEL% NEQ 0 (
    echo Error starting backend services. Please check docker-compose logs.
    exit /b 1
)

REM Wait for backend services to be ready
echo Waiting for backend services to be ready...
timeout /t 5 /nobreak

REM Start the frontend and nginx
echo Starting frontend and nginx...
docker-compose up -d frontend nginx
if %ERRORLEVEL% NEQ 0 (
    echo Error starting frontend and nginx. Please check docker-compose logs.
    exit /b 1
)

echo ====================================================================
echo All services started. Service status:
docker ps
echo ====================================================================
echo To view service logs, run: docker logs -f [service_container_id]
echo ==================================================================== 