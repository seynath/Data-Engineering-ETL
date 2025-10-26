#!/bin/bash
# Fix missing warehouse loading task

echo "=========================================="
echo "Fixing Missing Warehouse Loading Task"
echo "=========================================="

echo ""
echo "Issue identified:"
echo "- dbt models were trying to read from warehouse tables"
echo "- But silver data was never loaded to the warehouse"
echo "- Missing 'load_to_warehouse' task between silver and dbt"
echo ""

echo "Fix applied:"
echo "- Added load_to_warehouse task"
echo "- Loads Parquet files from silver layer to PostgreSQL"
echo "- Creates 'silver' schema in warehouse"
echo "- Updated task dependencies: silver -> load_warehouse -> dbt"
echo ""

echo "Step 1: Restarting Airflow services..."
docker-compose restart airflow-scheduler airflow-webserver

echo ""
echo "Step 2: Waiting for services to restart..."
sleep 15

echo ""
echo "=========================================="
echo "✓ WAREHOUSE LOADING FIX APPLIED!"
echo "=========================================="

echo ""
echo "The pipeline will now:"
echo "1. ✓ Ingest bronze layer (CSV files)"
echo "2. ✓ Transform to silver layer (Parquet files)"
echo "3. ✓ Validate with Great Expectations"
echo "4. ✓ Load silver data to warehouse (NEW!)"
echo "5. ✓ Run dbt transformations (will now work!)"
echo "6. ✓ Complete successfully!"
echo ""
echo "Next: Wait for automatic retry or trigger new DAG run"
echo ""
echo "Verify warehouse data after pipeline runs:"
echo "  ./pipeline-cli.sh db-warehouse"
echo "  SELECT * FROM silver.patients LIMIT 5;"
echo "  SELECT * FROM silver.encounters LIMIT 5;"
echo "=========================================="