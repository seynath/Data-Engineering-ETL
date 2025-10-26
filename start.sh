#!/bin/bash
# Complete startup script for Healthcare ETL Pipeline

set -e

echo "=========================================="
echo "Healthcare ETL Pipeline Startup"
echo "=========================================="

# Step 1: Clean up any existing containers
echo ""
echo "Step 1: Cleaning up existing containers..."
docker-compose down -v 2>/dev/null || true

# Step 2: Start database services first
echo ""
echo "Step 2: Starting database services..."
docker-compose up -d postgres warehouse-db

# Wait for databases to be healthy
echo "Waiting for databases to be ready..."
sleep 15

# Step 3: Initialize Airflow
echo ""
echo "Step 3: Initializing Airflow..."
docker-compose run --rm airflow-init

# Step 4: Start all services
echo ""
echo "Step 4: Starting all services..."
docker-compose up -d

# Step 5: Wait for services to be healthy
echo ""
echo "Step 5: Waiting for services to start..."
sleep 30

# Step 6: Show status
echo ""
echo "=========================================="
echo "Service Status:"
echo "=========================================="
docker-compose ps

echo ""
echo "=========================================="
echo "Access URLs:"
echo "=========================================="
echo "Airflow UI:  http://localhost:8080"
echo "  Username: airflow"
echo "  Password: airflow"
echo ""
echo "Superset UI: http://localhost:8088"
echo "  Username: admin"
echo "  Password: admin"
echo ""
echo "PostgreSQL (Airflow): localhost:5432"
echo "PostgreSQL (Warehouse): localhost:5433"
echo "=========================================="
echo ""
echo "To view logs: docker-compose logs -f [service-name]"
echo "To stop: docker-compose down"
echo "=========================================="
