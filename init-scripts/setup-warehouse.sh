#!/bin/bash
# Setup script for healthcare warehouse database
# This script initializes the warehouse database and populates the date dimension

set -e

echo "=========================================="
echo "Healthcare Warehouse Setup Script"
echo "=========================================="

# Load environment variables
if [ -f .env ]; then
    echo "Loading environment variables from .env file..."
    export $(cat .env | grep -v '^#' | xargs)
fi

# Set defaults
POSTGRES_HOST=${POSTGRES_HOST:-localhost}
POSTGRES_PORT=${POSTGRES_PORT:-5433}
POSTGRES_DB=${POSTGRES_DB:-healthcare_warehouse}
POSTGRES_USER=${POSTGRES_USER:-etl_user}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-etl_password}

echo ""
echo "Configuration:"
echo "  Host: $POSTGRES_HOST"
echo "  Port: $POSTGRES_PORT"
echo "  Database: $POSTGRES_DB"
echo "  User: $POSTGRES_USER"
echo ""

# Wait for warehouse database to be ready
echo "Waiting for warehouse database to be ready..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DB -c '\q' 2>/dev/null; then
        echo "Warehouse database is ready!"
        break
    fi
    attempt=$((attempt + 1))
    echo "Attempt $attempt/$max_attempts - Database not ready yet, waiting..."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "ERROR: Warehouse database did not become ready in time"
    exit 1
fi

# Check if tables exist
echo ""
echo "Checking database schema..."
table_count=$(PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DB -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';" | xargs)

echo "Found $table_count tables in the database"

if [ "$table_count" -eq "0" ]; then
    echo "WARNING: No tables found. Database initialization may have failed."
    echo "Tables should be created automatically via docker-entrypoint-initdb.d scripts"
    exit 1
fi

# Populate dim_date table
echo ""
echo "Populating date dimension table..."
if command -v python3 &> /dev/null; then
    python3 populate_dim_date.py
elif command -v python &> /dev/null; then
    python populate_dim_date.py
else
    echo "WARNING: Python not found. Please run 'python populate_dim_date.py' manually"
fi

# Verify setup
echo ""
echo "Verifying database setup..."
PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DB << EOF
\echo 'Database Tables:'
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
ORDER BY table_name;

\echo ''
\echo 'Dimension Tables Row Counts:'
SELECT 'dim_patient' as table_name, COUNT(*) as row_count FROM dim_patient
UNION ALL
SELECT 'dim_provider', COUNT(*) FROM dim_provider
UNION ALL
SELECT 'dim_date', COUNT(*) FROM dim_date
UNION ALL
SELECT 'dim_diagnosis', COUNT(*) FROM dim_diagnosis
UNION ALL
SELECT 'dim_procedure', COUNT(*) FROM dim_procedure
UNION ALL
SELECT 'dim_medication', COUNT(*) FROM dim_medication;

\echo ''
\echo 'Fact Tables Row Counts:'
SELECT 'fact_encounter' as table_name, COUNT(*) as row_count FROM fact_encounter
UNION ALL
SELECT 'fact_billing', COUNT(*) FROM fact_billing
UNION ALL
SELECT 'fact_lab_test', COUNT(*) FROM fact_lab_test
UNION ALL
SELECT 'fact_denial', COUNT(*) FROM fact_denial;
EOF

echo ""
echo "=========================================="
echo "Warehouse setup complete!"
echo "=========================================="
echo ""
echo "You can now:"
echo "  1. Run the ETL pipeline from Airflow UI (http://localhost:8080)"
echo "  2. Access Superset dashboards (http://localhost:8088)"
echo "  3. Query the warehouse directly:"
echo "     psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DB"
echo ""
