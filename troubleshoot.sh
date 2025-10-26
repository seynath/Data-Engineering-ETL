#!/bin/bash
# Troubleshooting script for Healthcare ETL Pipeline

echo "=========================================="
echo "Healthcare ETL Pipeline Diagnostics"
echo "=========================================="

echo ""
echo "1. Container Status:"
echo "----------------------------------------"
docker-compose ps

echo ""
echo "2. Container Health:"
echo "----------------------------------------"
docker ps --format "table {{.Names}}\t{{.Status}}"

echo ""
echo "3. Recent Logs (Last 20 lines per service):"
echo "----------------------------------------"

for service in postgres warehouse-db airflow-init airflow-webserver airflow-scheduler superset; do
    echo ""
    echo "=== $service ==="
    docker-compose logs --tail=20 $service 2>/dev/null || echo "Service not running"
done

echo ""
echo "4. Network Status:"
echo "----------------------------------------"
docker network inspect healthcare-etl-network 2>/dev/null | grep -A 5 "Containers" || echo "Network not found"

echo ""
echo "5. Volume Status:"
echo "----------------------------------------"
docker volume ls | grep data-engineering-etl

echo ""
echo "=========================================="
echo "Common Issues & Solutions:"
echo "=========================================="
echo "1. airflow-init unhealthy:"
echo "   - Run: docker-compose down -v"
echo "   - Run: ./start.sh"
echo ""
echo "2. Port already in use:"
echo "   - Check: lsof -i :8080 (or :5432, :5433, :8088)"
echo "   - Kill process or change port in docker-compose.yml"
echo ""
echo "3. Permission errors:"
echo "   - Run: sudo chown -R \$USER:0 airflow/"
echo "=========================================="
