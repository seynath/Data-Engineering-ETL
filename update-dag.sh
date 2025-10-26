#!/bin/bash
# Quick script to verify DAG updates (for bind-mounted volumes)

echo "=========================================="
echo "DAG Update Verification"
echo "=========================================="

echo ""
echo "Since your docker-compose.yml uses bind mounts, DAG changes"
echo "are automatically visible to Airflow containers."
echo ""

# Find running Airflow container
AIRFLOW_CONTAINER=$(docker ps --filter "name=airflow-scheduler" --format "{{.Names}}" | head -1)

if [ -n "$AIRFLOW_CONTAINER" ]; then
    echo "✓ Found running container: $AIRFLOW_CONTAINER"
    echo ""
    echo "Checking DAG file in container..."
    docker exec $AIRFLOW_CONTAINER ls -lh /opt/airflow/dags/healthcare_etl_dag.py
    
    echo ""
    echo "Recent changes to DAG file on host:"
    ls -lh airflow/dags/healthcare_etl_dag.py
    
    echo ""
    echo "=========================================="
    echo "DAG Refresh Information:"
    echo "=========================================="
    echo "Airflow automatically scans for DAG changes every 5 minutes."
    echo ""
    echo "To force immediate refresh:"
    echo "1. Go to Airflow UI: http://localhost:8080"
    echo "2. Click 'Browse' → 'Refresh'"
    echo ""
    echo "Or check scheduler logs for parsing status:"
    echo "  docker-compose logs airflow-scheduler | grep -i 'dag' | tail -20"
    echo "=========================================="
else
    echo "⚠ No running Airflow containers found!"
    echo "Please start services first: docker-compose up -d"
    exit 1
fi
