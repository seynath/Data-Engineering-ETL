#!/bin/bash

# Setup Superset Connection to Data Warehouse
echo "Setting up Superset connection to Healthcare Warehouse..."

# Wait for Superset to be ready
echo "Waiting for Superset to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8088/health &>/dev/null; then
        echo "✓ Superset is ready"
        break
    fi
    sleep 2
done

echo ""
echo "=========================================="
echo "Superset Setup Instructions"
echo "=========================================="
echo ""
echo "1. Open Superset: http://localhost:8088"
echo "   Login: admin / admin"
echo ""
echo "2. Add Database Connection:"
echo "   - Click Settings → Database Connections"
echo "   - Click + Database"
echo "   - Select PostgreSQL"
echo "   - Use this connection string:"
echo ""
echo "   postgresql://etl_user:etl_password@warehouse-db:5432/healthcare_warehouse"
echo ""
echo "3. Add Datasets:"
echo "   - Go to Data → Datasets"
echo "   - Click + Dataset"
echo "   - Select: Healthcare Warehouse / public_public / [table_name]"
echo "   - Add these tables:"
echo "     • dim_patient"
echo "     • dim_provider"
echo "     • dim_diagnosis"
echo "     • fact_encounter"
echo "     • fact_billing"
echo "     • fact_lab_test"
echo "     • fact_denial"
echo ""
echo "4. Create Charts and Dashboards!"
echo ""
echo "=========================================="
