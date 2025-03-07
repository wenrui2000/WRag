@echo off
echo REBUILDING APPLICATION SERVICES (INDEXING, QUERY)

echo STOPPING APPLICATION SERVICES...
docker-compose stop indexing_service query_service frontend nginx

echo REMOVING APPLICATION SERVICE CONTAINERS...
docker-compose rm -f indexing_service query_service 

echo REBUILDING APPLICATION SERVICES...
docker-compose build indexing_service query_service 

echo STARTING APPLICATION SERVICES...
docker-compose up -d indexing_service query_service frontend nginx
