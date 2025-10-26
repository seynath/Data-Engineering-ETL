#!/bin/bash

# Healthcare ETL Pipeline - Status Check Script

echo "=========================================="
echo "Healthcare ETL Pipeline - Status Check"
echo "=========================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Check container status
echo "📦 Container Status:"
echo "-------------------------------------------"
docker-compose ps
echo ""

# Check service health
echo "🏥 Service Health:"
echo "-------------------------------------------"

# Function to check if service is accessible
check_service() {
    local name=$1
    local url=$2
    local expected=$3
    
    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "$expected"; then
        echo "✅ $name is accessible at $url"
    else
        echo "⏳ $name is starting... (check $url in a moment)"
    fi
}

# Check Airflow
check_service "Airflow" "http://localhost:8080/health" "200"

# Check Superset
check_service "Superset" "http://localhost:8088/health" "200"

# Check PostgreSQL
if docker-compose exec -T warehouse-db psql -U etl_user -d healthcare_warehouse -c "SELECT 1;" > /dev/null 2>&1; then
    echo "✅ PostgreSQL warehouse is accessible"
else
    echo "⏳ PostgreSQL warehouse is starting..."
fi

echo ""
echo "=========================================="
echo "Access URLs:"
echo "=========================================="
echo "🌐 Airflow:   http://localhost:8080"
echo "   Username: airflow"
echo "   Password: airflow"
echo ""
echo "📊 Superset:  http://localhost:8088"
echo "   Username: admin"
echo "   Password: admin"
echo ""
echo "🗄️  PostgreSQL: localhost:5433"
echo "   Database: healthcare_warehouse"
echo "   Username: etl_user"
echo "   Password: etl_password"
echo "=========================================="
echo ""

# Check if all services are healthy
healthy_count=$(docker-compose ps | grep -c "healthy")
total_services=5  # airflow-webserver, airflow-scheduler, postgres, warehouse-db, superset

if [ "$healthy_count" -eq "$total_services" ]; then
    echo "🎉 All services are healthy and ready!"
    echo ""
    echo "Next steps:"
    echo "1. Open Airflow: http://localhost:8080"
    echo "2. Find 'healthcare_etl_pipeline' DAG"
    echo "3. Click the play button to trigger the pipeline"
else
    echo "⏳ Services are still starting up..."
    echo "   Please wait 2-3 minutes and run this script again."
    echo ""
    echo "   Run: ./check_status.sh"
fi
