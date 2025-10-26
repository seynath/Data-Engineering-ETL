#!/bin/bash
# Fix directory permissions for Airflow

echo "Fixing directory permissions..."

# Create directories if they don't exist
mkdir -p data/bronze data/silver airflow/logs airflow/dags airflow/plugins dataset config logs

# Fix permissions
echo "Setting permissions on data directories..."
chmod -R 777 data/ 2>/dev/null || sudo chmod -R 777 data/

echo "Setting permissions on airflow directories..."
chmod -R 777 airflow/logs/ 2>/dev/null || sudo chmod -R 777 airflow/logs/

echo "Setting permissions on logs directory..."
chmod -R 777 logs/ 2>/dev/null || sudo chmod -R 777 logs/

echo ""
echo "Permissions fixed!"
echo ""
echo "Directory structure:"
ls -la data/ airflow/

echo ""
echo "You can now run: ./pipeline-cli.sh start"
