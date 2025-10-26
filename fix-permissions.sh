#!/bin/bash
# Fix directory permissions for Airflow

echo "Fixing directory permissions..."

# Create all directories if they don't exist
echo "Creating directories..."
mkdir -p data/bronze data/silver \
         airflow/logs airflow/dags airflow/plugins \
         dataset config \
         logs logs/alerts \
         great_expectations/uncommitted/validations \
         great_expectations/uncommitted/data_docs \
         dbt_project

# Fix permissions on all writable directories
echo "Setting permissions on all directories..."
DIRS_TO_FIX="data/ airflow/logs/ logs/ great_expectations/ config/ dbt_project/"

if chmod -R 777 $DIRS_TO_FIX 2>/dev/null; then
    echo "✓ Permissions fixed without sudo"
else
    echo "Need sudo for permissions..."
    sudo chmod -R 777 $DIRS_TO_FIX
    echo "✓ Permissions fixed with sudo"
fi

# Ensure dataset is readable
echo "Setting read permissions on dataset..."
chmod -R 755 dataset/ 2>/dev/null || sudo chmod -R 755 dataset/

echo ""
echo "Permissions fixed!"
echo ""
echo "Directory structure:"
ls -la data/ airflow/

echo ""
echo "You can now run: ./pipeline-cli.sh start"
