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
echo "Step 2: Creating all required directories..."
mkdir -p data/bronze data/silver \
         airflow/logs airflow/dags airflow/plugins \
         dataset config \
         logs logs/alerts \
         great_expectations/uncommitted/validations \
         great_expectations/uncommitted/data_docs \
         dbt_project

echo ""
echo "Step 3: Fixing permissions on all directories..."
echo "Attempting to fix permissions (may require sudo)..."

# List of directories that need write permissions
DIRS_TO_FIX="data/ airflow/logs/ logs/ great_expectations/ config/ dbt_project/"

# Try without sudo first
if chmod -R 777 $DIRS_TO_FIX 2>/dev/null; then
    echo "✓ Permissions fixed"
else
    echo "Need sudo for permissions..."
    sudo chmod -R 777 $DIRS_TO_FIX
    echo "✓ Permissions fixed with sudo"
fi

# Also ensure dataset directory is readable
chmod -R 755 dataset/ 2>/dev/null || sudo chmod -R 755 dataset/

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
