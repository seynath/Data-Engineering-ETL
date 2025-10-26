#!/bin/bash
# Initialize Airflow metadata database
# This script is run by the airflow-init service in docker-compose

set -e

echo "Initializing Airflow metadata database..."

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
while ! pg_isready -h postgres -U airflow -d airflow > /dev/null 2>&1; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 2
done

echo "PostgreSQL is ready!"

# Initialize Airflow database
echo "Running Airflow database migrations..."
airflow db migrate

# Create admin user
echo "Creating Airflow admin user..."
airflow users create \
    --username "${_AIRFLOW_WWW_USER_USERNAME:-airflow}" \
    --firstname "Admin" \
    --lastname "User" \
    --role "Admin" \
    --email "admin@example.com" \
    --password "${_AIRFLOW_WWW_USER_PASSWORD:-airflow}" || true

echo "Airflow initialization complete!"
