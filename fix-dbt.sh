#!/bin/bash
# Fix dbt deps issue

echo "=========================================="
echo "Fixing dbt Dependencies Issue"
echo "=========================================="

echo ""
echo "What was fixed:"
echo "- Added 'dbt deps' task before dbt_run_staging"
echo "- This installs package dependencies from packages.yml"
echo "- Task runs automatically before any dbt transformations"
echo ""

echo "Step 1: Restarting Airflow services..."
docker-compose restart airflow-scheduler airflow-webserver

echo ""
echo "Step 2: Waiting for services to restart..."
sleep 15

echo ""
echo "=========================================="
echo "✓ DBT FIX APPLIED!"
echo "=========================================="

echo ""
echo "The dbt pipeline will now:"
echo "1. Run 'dbt deps' to install packages"
echo "2. Run staging models"
echo "3. Run dimension models"
echo "4. Run fact models"
echo "5. Run tests"
echo ""
echo "Next: Wait for automatic retry or trigger new DAG run"
echo "=========================================="
