#!/bin/bash
# Quick fix script for pip permission error

echo "=========================================="
echo "Fixing Pip Permission Error"
echo "=========================================="

echo ""
echo "Step 1: Stopping all containers..."
docker-compose down -v

echo ""
echo "Step 2: Removing old Airflow images..."
docker rmi healthcare-etl-airflow:latest 2>/dev/null || echo "No old image to remove"

echo ""
echo "Step 3: Building new custom Airflow image..."
echo "This may take 2-3 minutes on first build..."
docker-compose build

echo ""
echo "Step 4: Starting services with new image..."
./start.sh

echo ""
echo "=========================================="
echo "Fix Applied!"
echo "=========================================="
echo ""
echo "Check for errors:"
echo "  docker-compose logs airflow-init | grep -i error"
echo ""
echo "If no errors, you're good to go!"
echo "Open Airflow: http://localhost:8080"
echo "=========================================="
