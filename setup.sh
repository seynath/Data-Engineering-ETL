#!/bin/bash
# Master setup script for Healthcare ETL Pipeline
# This script sets up the entire local development environment

set -e

echo "=========================================="
echo "Healthcare ETL Pipeline Setup"
echo "=========================================="
echo ""

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed. Please install Docker Desktop."
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "ERROR: Docker Compose is not installed. Please install Docker Compose."
    exit 1
fi

echo "✓ Docker is installed"
echo "✓ Docker Compose is installed"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "✓ Created .env file"
    echo "  You can edit .env to customize configuration"
else
    echo "✓ .env file already exists"
fi
echo ""

# Create required directories
echo "Creating required directories..."
mkdir -p airflow/dags airflow/logs airflow/plugins
mkdir -p data/bronze data/silver
mkdir -p logs/alerts
mkdir -p great_expectations/uncommitted
echo "✓ Directories created"
echo ""

# Set proper permissions for Airflow
echo "Setting permissions for Airflow directories..."
AIRFLOW_UID=${AIRFLOW_UID:-50000}
if [ "$(uname)" == "Darwin" ] || [ "$(uname)" == "Linux" ]; then
    # On macOS and Linux, set ownership
    sudo chown -R $AIRFLOW_UID:0 airflow/logs airflow/dags airflow/plugins 2>/dev/null || {
        echo "  Note: Could not set ownership (may require sudo). This is usually fine."
    }
fi
echo "✓ Permissions configured"
echo ""

# Start Docker Compose services
echo "Starting Docker Compose services..."
echo "This may take a few minutes on first run..."
echo ""

# Use docker compose (v2) or docker-compose (v1)
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

$DOCKER_COMPOSE up -d

echo ""
echo "Waiting for services to be healthy..."
echo "This may take 2-3 minutes..."
echo ""

# Wait for services to be healthy
max_wait=180
elapsed=0
while [ $elapsed -lt $max_wait ]; do
    if $DOCKER_COMPOSE ps | grep -q "unhealthy"; then
        echo "  Waiting for services to become healthy... (${elapsed}s/${max_wait}s)"
        sleep 10
        elapsed=$((elapsed + 10))
    else
        echo "✓ All services are healthy!"
        break
    fi
done

if [ $elapsed -ge $max_wait ]; then
    echo "WARNING: Some services may not be fully healthy yet"
    echo "You can check status with: $DOCKER_COMPOSE ps"
fi

echo ""
echo "Initializing warehouse database..."
sleep 5  # Give warehouse-db a moment to finish initialization

# Run warehouse setup script
if [ -f init-scripts/setup-warehouse.sh ]; then
    bash init-scripts/setup-warehouse.sh
else
    echo "WARNING: setup-warehouse.sh not found, skipping warehouse initialization"
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Services are now running:"
echo ""
echo "  Airflow UI:       http://localhost:8080"
echo "    Username: airflow"
echo "    Password: airflow"
echo ""
echo "  Superset:         http://localhost:8088"
echo "    Username: admin"
echo "    Password: admin"
echo ""
echo "  PostgreSQL Warehouse: localhost:5433"
echo "    Database: healthcare_warehouse"
echo "    Username: etl_user"
echo "    Password: etl_password"
echo ""
echo "Next steps:"
echo "  1. Place your CSV files in the 'dataset/' directory"
echo "  2. Open Airflow UI and trigger the 'healthcare_etl_pipeline' DAG"
echo "  3. Monitor the pipeline execution in Airflow"
echo "  4. View results in Superset dashboards"
echo ""
echo "Useful commands:"
echo "  View logs:        $DOCKER_COMPOSE logs -f [service-name]"
echo "  Stop services:    $DOCKER_COMPOSE down"
echo "  Restart services: $DOCKER_COMPOSE restart"
echo "  View status:      $DOCKER_COMPOSE ps"
echo ""
