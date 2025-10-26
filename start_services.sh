#!/bin/bash

# Healthcare ETL Pipeline - Service Startup Script
# This script properly initializes and starts all services

set -e

echo "=========================================="
echo "Healthcare ETL Pipeline - Starting Services"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Check Docker is running
echo -e "${YELLOW}Step 1: Checking Docker...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker Desktop.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker is running${NC}"
echo ""

# Step 2: Create required directories
echo -e "${YELLOW}Step 2: Creating directories...${NC}"
mkdir -p airflow/{dags,logs,plugins}
mkdir -p data/{bronze,silver}
mkdir -p logs/alerts
echo -e "${GREEN}✅ Directories created${NC}"
echo ""

# Step 3: Set correct permissions
echo -e "${YELLOW}Step 3: Setting permissions...${NC}"
chmod -R 777 airflow/logs
chmod -R 777 data
chmod -R 777 logs
echo -e "${GREEN}✅ Permissions set${NC}"
echo ""

# Step 4: Start database services first
echo -e "${YELLOW}Step 4: Starting databases...${NC}"
docker-compose up -d postgres warehouse-db
echo "Waiting for databases to be healthy (10 seconds)..."
sleep 10
echo -e "${GREEN}✅ Databases started${NC}"
echo ""

# Step 5: Initialize Airflow
echo -e "${YELLOW}Step 5: Initializing Airflow...${NC}"
docker-compose run --rm airflow-init || {
    echo -e "${YELLOW}⚠️  Airflow already initialized, continuing...${NC}"
}
echo -e "${GREEN}✅ Airflow initialized${NC}"
echo ""

# Step 6: Start Airflow services
echo -e "${YELLOW}Step 6: Starting Airflow services...${NC}"
docker-compose up -d airflow-webserver airflow-scheduler
echo "Waiting for Airflow to start (15 seconds)..."
sleep 15
echo -e "${GREEN}✅ Airflow services started${NC}"
echo ""

# Step 7: Start Superset
echo -e "${YELLOW}Step 7: Starting Superset...${NC}"
docker-compose up -d superset
echo "Waiting for Superset to initialize (20 seconds)..."
sleep 20
echo -e "${GREEN}✅ Superset started${NC}"
echo ""

# Step 8: Check service status
echo -e "${YELLOW}Step 8: Checking service status...${NC}"
docker-compose ps
echo ""

# Step 9: Display access information
echo "=========================================="
echo -e "${GREEN}🎉 Services Started Successfully!${NC}"
echo "=========================================="
echo ""
echo "Access URLs:"
echo "  🌐 Airflow:   http://localhost:8080"
echo "     Username: airflow"
echo "     Password: airflow"
echo ""
echo "  📊 Superset:  http://localhost:8088"
echo "     Username: admin"
echo "     Password: admin"
echo ""
echo "  🗄️  PostgreSQL: localhost:5433"
echo "     Database: healthcare_warehouse"
echo "     Username: etl_user"
echo "     Password: etl_password"
echo ""
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Open Airflow: http://localhost:8080"
echo "2. Find 'healthcare_etl_pipeline' DAG"
echo "3. Click the play button to trigger the pipeline"
echo ""
echo "To check status: ./check_status.sh"
echo "To stop services: docker-compose down"
echo "=========================================="
