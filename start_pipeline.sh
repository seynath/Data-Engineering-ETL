#!/bin/bash

# Healthcare ETL Pipeline - Complete Startup Script
# This script starts all services and runs the pipeline

set -e  # Exit on error

echo "=========================================="
echo "Healthcare ETL Pipeline Startup"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "ℹ $1"
}

# Step 1: Check prerequisites
echo "Step 1: Checking prerequisites..."
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker Desktop first."
    exit 1
fi

if ! docker info &> /dev/null; then
    print_error "Docker is not running. Please start Docker Desktop."
    exit 1
fi

print_success "Docker is running"

# Step 2: Check if .env exists
echo ""
echo "Step 2: Checking environment configuration..."
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        print_warning ".env file not found. Creating from .env.example..."
        cp .env.example .env
        print_success "Created .env file"
    else
        print_error ".env.example not found. Cannot create .env file."
        exit 1
    fi
else
    print_success ".env file exists"
fi

# Step 3: Create required directories
echo ""
echo "Step 3: Creating required directories..."
mkdir -p airflow/dags airflow/logs airflow/plugins
mkdir -p data/bronze data/silver
mkdir -p logs/alerts
mkdir -p dataset
print_success "Directories created"

# Step 4: Stop any existing containers
echo ""
echo "Step 4: Stopping any existing containers..."
docker-compose down 2>/dev/null || true
print_success "Cleaned up existing containers"

# Step 5: Start services
echo ""
echo "Step 5: Starting Docker services..."
print_info "This may take 2-3 minutes on first run..."
docker-compose up -d

# Step 6: Wait for services to be healthy
echo ""
echo "Step 6: Waiting for services to be ready..."

# Wait for PostgreSQL (Airflow metadata)
print_info "Waiting for Airflow database..."
for i in {1..30}; do
    if docker exec healthcare-etl-postgres pg_isready -U airflow &>/dev/null; then
        print_success "Airflow database is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        print_error "Airflow database failed to start"
        exit 1
    fi
    sleep 2
done

# Wait for Warehouse database
print_info "Waiting for warehouse database..."
for i in {1..30}; do
    if docker exec healthcare-etl-warehouse-db pg_isready -U etl_user &>/dev/null; then
        print_success "Warehouse database is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        print_error "Warehouse database failed to start"
        exit 1
    fi
    sleep 2
done

# Wait for Airflow webserver
print_info "Waiting for Airflow webserver..."
for i in {1..60}; do
    if curl -s http://localhost:8080/health &>/dev/null; then
        print_success "Airflow webserver is ready"
        break
    fi
    if [ $i -eq 60 ]; then
        print_error "Airflow webserver failed to start"
        exit 1
    fi
    sleep 3
done

# Step 7: Check if data exists
echo ""
echo "Step 7: Checking for data files..."
CSV_COUNT=$(ls -1 dataset/*.csv 2>/dev/null | wc -l)
if [ $CSV_COUNT -eq 0 ]; then
    print_warning "No CSV files found in dataset/ directory"
    print_info "Please add your CSV files to the dataset/ directory before running the pipeline"
    print_info "Required files: patients.csv, encounters.csv, diagnoses.csv, procedures.csv,"
    print_info "                medications.csv, lab_tests.csv, claims_and_billing.csv,"
    print_info "                providers.csv, denials.csv"
else
    print_success "Found $CSV_COUNT CSV files in dataset/"
fi

# Step 8: Display service status
echo ""
echo "=========================================="
echo "Service Status"
echo "=========================================="
docker-compose ps

# Step 9: Display access information
echo ""
echo "=========================================="
echo "Access Information"
echo "=========================================="
echo ""
echo "🌐 Airflow UI:    http://localhost:8080"
echo "   Username:      airflow"
echo "   Password:      airflow"
echo ""
echo "📊 Superset UI:   http://localhost:8088"
echo "   Username:      admin"
echo "   Password:      admin"
echo ""
echo "🗄️  PostgreSQL:    localhost:5432"
echo "   Database:      healthcare_warehouse"
echo "   Username:      etl_user"
echo "   Password:      etl_password"
echo ""

# Step 10: Offer to trigger pipeline
echo "=========================================="
echo "Pipeline Execution"
echo "=========================================="
echo ""

if [ $CSV_COUNT -gt 0 ]; then
    read -p "Do you want to trigger the ETL pipeline now? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        print_info "Triggering healthcare_etl_pipeline DAG..."
        sleep 2  # Give Airflow a moment to fully initialize
        
        docker exec healthcare-etl-airflow-webserver airflow dags unpause healthcare_etl_pipeline 2>/dev/null || true
        docker exec healthcare-etl-airflow-webserver airflow dags trigger healthcare_etl_pipeline
        
        print_success "Pipeline triggered!"
        echo ""
        print_info "Monitor progress at: http://localhost:8080"
        print_info "Expected runtime: 10-15 minutes"
        echo ""
        print_info "To view logs in real-time, run:"
        echo "   docker-compose logs -f airflow-scheduler"
    else
        echo ""
        print_info "You can trigger the pipeline later from Airflow UI or run:"
        echo "   docker exec healthcare-etl-airflow-webserver airflow dags trigger healthcare_etl_pipeline"
    fi
else
    print_warning "Add CSV files to dataset/ directory first, then trigger the pipeline from Airflow UI"
fi

echo ""
echo "=========================================="
echo "Useful Commands"
echo "=========================================="
echo ""
echo "View logs:           docker-compose logs -f"
echo "Stop services:       docker-compose down"
echo "Restart services:    docker-compose restart"
echo "Check status:        docker-compose ps"
echo "Trigger pipeline:    docker exec healthcare-etl-airflow-webserver airflow dags trigger healthcare_etl_pipeline"
echo "Connect to DB:       docker exec -it healthcare-etl-warehouse-db psql -U etl_user -d healthcare_warehouse"
echo ""
echo "=========================================="
print_success "Setup complete! Your pipeline is ready."
echo "=========================================="
echo ""
