#!/bin/bash
# Verify all directory permissions are correct

echo "=========================================="
echo "Permission Verification"
echo "=========================================="

echo ""
echo "Checking directory existence and permissions..."
echo ""

# List of directories that should exist and be writable
REQUIRED_DIRS=(
    "data/bronze"
    "data/silver"
    "airflow/logs"
    "logs"
    "logs/alerts"
    "great_expectations/uncommitted/validations"
    "great_expectations/uncommitted/data_docs"
    "config"
    "dbt_project"
)

ALL_OK=true

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        PERMS=$(stat -f "%Lp" "$dir" 2>/dev/null || stat -c "%a" "$dir" 2>/dev/null)
        if [ -w "$dir" ]; then
            echo "✓ $dir (permissions: $PERMS) - OK"
        else
            echo "✗ $dir (permissions: $PERMS) - NOT WRITABLE"
            ALL_OK=false
        fi
    else
        echo "✗ $dir - DOES NOT EXIST"
        ALL_OK=false
    fi
done

echo ""
echo "=========================================="

if [ "$ALL_OK" = true ]; then
    echo "✓ All directories OK!"
    echo ""
    echo "You can now run the pipeline:"
    echo "  ./pipeline-cli.sh trigger-dag"
else
    echo "✗ Some directories have issues"
    echo ""
    echo "Run this to fix:"
    echo "  ./pipeline-cli.sh quick-fix"
    echo "  docker-compose restart"
fi

echo "=========================================="
