#!/bin/bash
# Complete fix for all permission and setup issues

echo "=========================================="
echo "Complete Healthcare ETL Pipeline Fix"
echo "=========================================="

echo ""
echo "This script will:"
echo "1. Fix directory permissions"
echo "2. Stop existing containers"
echo "3. Build custom Airflow image"
echo "4. Start all services"
echo ""
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "Step 1: Setting AIRFLOW_UID..."
export AIRFLOW_UID=50000
echo "AIRFLOW_UID set to 50000"

echo ""
echo "Step 2: Creating directories..."
mkdir -p data/bronze data/silver airflow/logs airflow/dags airflow/plugins dataset config logs

echo ""
echo "Step 3: Fixing permissions..."
echo "Attempting to fix permissions (may require sudo)..."

# Try without sudo first
if chmod -R 777 data/ airflow/logs/ logs/ 2>/dev/null; then
    echo "✓ Permissions fixed"
else
    echo "Need sudo for permissions..."
    sudo chmod -R 777 data/ airflow/logs/ logs/
    echo "✓ Permissions fixed with sudo"
fi

echo ""
echo "Step 4: Stopping existing containers..."
docker-compose down -v

echo ""
echo "Step 5: Removing old images..."
docker rmi healthcare-etl-airflow:latest 2>/dev/null || echo "No old image to remove"

echo ""
echo "Step 6: Building custom Airflow image..."
echo "This may take 3-5 minutes..."
docker-compose build

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Build failed! Check the error above."
    exit 1
fi

echo ""
echo "Step 7: Starting database services..."
docker-compose up -d postgres warehouse-db

echo ""
echo "Waiting for databases to be ready..."
sleep 15

echo ""
echo "Step 8: Initializing Airflow..."
docker-compose run --rm airflow-init

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Airflow initialization failed!"
    echo "Check logs: docker-compose logs airflow-init"
    exit 1
fi

echo ""
echo "Step 9: Starting all services..."
docker-compose up -d

echo ""
echo "Step 10: Waiting for services to start..."
sleep 30

echo ""
echo "=========================================="
echo "✓ Complete Fix Applied!"
echo "=========================================="

echo ""
echo "Checking service status..."
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
echo "=========================================="

echo ""
echo "To check for errors:"
echo "  docker-compose logs airflow-scheduler | tail -50"
echo ""
echo "To trigger the pipeline:"
echo "  ./pipeline-cli.sh trigger-dag"
echo "=========================================="
