#!/bin/bash
# Check Airflow status and troubleshoot

echo "=========================================="
echo "Checking Airflow Status"
echo "=========================================="

echo ""
echo "Step 1: Container status..."
docker ps --format "table {{.Names}}\t{{.Status}}"

echo ""
echo "Step 2: Checking Airflow webserver logs..."
echo "Last 20 lines of webserver logs:"
docker-compose logs --tail=20 airflow-webserver

echo ""
echo "Step 3: Checking Airflow scheduler logs..."
echo "Last 20 lines of scheduler logs:"
docker-compose logs --tail=20 airflow-scheduler

echo ""
echo "Step 4: Testing Airflow UI connection..."
echo "Checking if Airflow UI is responding..."
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080 || echo "Connection failed"

echo ""
echo "Step 5: Checking if DAGs are loaded..."
docker exec healthcare-etl-airflow-scheduler airflow dags list 2>/dev/null | grep healthcare_etl_pipeline || echo "DAG not found"

echo ""
echo "=========================================="
echo "Troubleshooting Steps:"
echo "=========================================="
echo "1. Try accessing Airflow UI: http://localhost:8080"
echo "2. If it doesn't load, wait 30 seconds and try again"
echo "3. Check logs above for any errors"
echo "4. If still issues, restart: docker-compose restart airflow-webserver"
echo "=========================================="