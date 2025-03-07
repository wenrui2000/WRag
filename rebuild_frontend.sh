#!/bin/bash
set -e

echo "Stopping frontend service..."
docker-compose stop frontend

echo "Rebuilding frontend service..."
docker-compose build frontend

echo "Starting frontend service..."
docker-compose up -d frontend

echo "Frontend service has been rebuilt and restarted." 