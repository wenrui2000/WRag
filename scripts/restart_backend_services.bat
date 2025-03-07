@echo off
echo ====================================================================
echo Restarting Backend Services (Indexing Service and Query Service)
echo ====================================================================

REM Stop the running services
echo Stopping existing services...
docker-compose stop indexing_service query_service
if %ERRORLEVEL% NEQ 0 (
    echo Error stopping services. Some services might not be running.
) else (
    echo Services stopped successfully.
)

REM Start the services again
echo Starting services...
docker-compose up -d indexing_service query_service
if %ERRORLEVEL% NEQ 0 (
    echo Error starting services. Please check docker-compose logs.
) else (
    echo Services started successfully.
)

echo ====================================================================
echo Restart completed. Service status:
docker ps --filter "name=wrag-app_indexing_service" --filter "name=wrag-app_query_service"
echo ====================================================================
echo To view service logs, run: docker logs -f [service_container_id]
echo ==================================================================== 