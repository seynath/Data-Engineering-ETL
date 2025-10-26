#!/bin/bash

# Superset Quick Setup Script
# This script automates the complete Superset setup process

set -e  # Exit on error

echo "=========================================="
echo "Healthcare ETL Pipeline - Superset Setup"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${NC}$1"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

print_success "Docker is running"

# Check if services are running
if ! docker-compose ps | grep -q "superset"; then
    print_warning "Superset service not found. Starting services..."
    docker-compose up -d
    print_info "Waiting for services to start (60 seconds)..."
    sleep 60
else
    print_success "Services are running"
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.8+ and try again."
    exit 1
fi

print_success "Python 3 is available"

# Check if requests library is installed
if ! python3 -c "import requests" 2>/dev/null; then
    print_warning "requests library not found. Installing..."
    pip3 install requests
fi

print_success "Python dependencies are installed"

echo ""
echo "=========================================="
echo "Step 1: Creating Database Connection"
echo "=========================================="
echo ""

python3 superset_setup.py --action setup --wait 30

if [ $? -ne 0 ]; then
    print_error "Failed to create database connection"
    print_info "Please check the logs above and try again"
    exit 1
fi

print_success "Database connection created"

echo ""
echo "=========================================="
echo "Step 2: Checking ETL Pipeline Status"
echo "=========================================="
echo ""

# Check if Gold layer tables exist
TABLE_COUNT=$(docker-compose exec -T warehouse-db psql -U etl_user -d healthcare_warehouse -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE'" 2>/dev/null | tr -d ' ')

if [ -z "$TABLE_COUNT" ] || [ "$TABLE_COUNT" -lt 10 ]; then
    print_warning "Gold layer tables not found or incomplete"
    print_info "You need to run the ETL pipeline first:"
    print_info "  docker-compose exec airflow-webserver airflow dags trigger healthcare_etl_pipeline"
    print_info ""
    print_info "After the pipeline completes, run this script again to create datasets and dashboards."
    exit 0
fi

print_success "Gold layer tables exist ($TABLE_COUNT tables found)"

echo ""
echo "=========================================="
echo "Step 3: Creating Datasets"
echo "=========================================="
echo ""

python3 superset_setup.py --action setup-datasets

if [ $? -ne 0 ]; then
    print_error "Failed to create datasets"
    print_info "Please check the logs above and try again"
    exit 1
fi

print_success "Datasets created"

echo ""
echo "=========================================="
echo "Step 4: Creating Dashboards"
echo "=========================================="
echo ""

python3 superset/create_dashboards.py --dashboard all

if [ $? -ne 0 ]; then
    print_warning "Some dashboards may not have been created"
    print_info "This is normal - some dashboards require manual creation"
fi

print_success "Dashboard creation completed"

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
print_success "Superset is ready to use"
echo ""
print_info "Access Superset at: http://localhost:8088"
print_info "  Username: admin"
print_info "  Password: admin"
echo ""
print_info "Available dashboards:"
print_info "  - Operational Overview"
print_info "  - Financial Analytics"
print_info "  - Clinical Insights (manual creation required)"
print_info "  - Provider Performance (manual creation required)"
print_info "  - Medication Analysis (manual creation required)"
echo ""
print_info "For detailed instructions, see:"
print_info "  - superset/SETUP_GUIDE.md"
print_info "  - superset/dashboards/dashboard_specifications.md"
echo ""
print_info "To test the setup:"
print_info "  python3 superset_setup.py --action test"
echo ""
