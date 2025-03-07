@echo off
docker build -t wrag-app_indexing_service:latest -f backend/Dockerfile.indexing backend
docker build -t wrag-app_query_service:latest -f backend/Dockerfile.query backend 