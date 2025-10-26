#!/bin/bash
echo "=========================================="
echo "Verifying Superset Setup"
echo "=========================================="

# Check if container is running
echo ""
echo "1. Container Status:"
docker ps | grep superset || echo "Container not running!"

# Check if it's listening
echo ""
echo "2. Checking if Superset is listening..."
docker logs healthcare-etl-superset 2>&1 | grep -i "listening at" || echo "Not listening yet"

# Check recent logs
echo ""
echo "3. Recent logs:"
docker logs healthcare-etl-superset 2>&1 | tail -10

echo ""
echo "=========================================="
echo "Login Information:"
echo "URL: http://localhost:8088 or http://YOUR_SERVER_IP:8088"
echo "Username: admin"
echo "Password: admin"
echo "=========================================="
