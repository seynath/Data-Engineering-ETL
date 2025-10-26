#!/bin/bash
# Fix Great Expectations validation configuration

echo "=========================================="
echo "Fixing Great Expectations Validation"
echo "=========================================="

echo ""
echo "Step 1: Restarting Airflow services to pick up new config..."
docker-compose restart airflow-scheduler airflow-webserver

echo ""
echo "Step 2: Waiting for services to restart..."
sleep 10

echo ""
echo "=========================================="
echo "✓ Configuration Updated!"
echo "=========================================="

echo ""
echo "The Great Expectations configuration has been fixed to:"
echo "- Recursively scan silver data directories"
echo "- Find Parquet files in dated subdirectories"
echo ""
echo "Next steps:"
echo "1. Go to Airflow UI: http://localhost:8080"
echo "2. Clear the failed validate_silver_layer task"
echo "3. Trigger the DAG again"
echo ""
echo "Or wait for the automatic retry (it will retry 4 times)"
echo "=========================================="
