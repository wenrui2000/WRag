@echo off
docker-compose rm -f base 
docker build -t wrag-app-base:latest -f backend/Dockerfile.base backend 