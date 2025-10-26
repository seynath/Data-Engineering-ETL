#!/bin/bash
# Quick permission fix without rebuilding

echo "Quick Permission Fix"
echo "===================="

echo ""
echo "Creating all missing directories..."
mkdir -p data/bronze data/silver \
         airflow/logs \
         logs logs/alerts \
         great_expectations/uncommitted/validations \
         great_expectations/uncommitted/data_docs \
         config \
         dbt_project

echo ""
echo "Fixing permissions on all directories..."
DIRS_TO_FIX="data/ airflow/logs/ logs/ great_expectations/ config/ dbt_project/"

chmod -R 777 $DIRS_TO_FIX 2>/dev/null || {
    echo "Need sudo for permissions..."
    sudo chmod -R 777 $DIRS_TO_FIX
}

echo ""
echo "✓ Permissions fixed!"
echo ""
echo "Now restart the services:"
echo "  docker-compose restart"
echo ""
echo "Or trigger the pipeline again in Airflow UI"
