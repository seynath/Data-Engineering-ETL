#!/bin/bash
echo "Fixing Superset login issues..."

# Stop Superset container
docker stop healthcare-etl-superset
docker rm healthcare-etl-superset

# Remove Superset volume to start fresh
docker volume rm healthcare-etl_superset-volume 2>/dev/null || echo "Volume not found, will be created"

# Start Superset again (it will initialize fresh)
cd /home/adata/Data-Engineering-ETL
docker-compose up -d superset

echo ""
echo "Waiting for Superset to initialize..."
sleep 30

# Check logs
echo ""
echo "Checking Superset logs:"
docker logs healthcare-etl-superset --tail 50

echo ""
echo "=========================================="
echo "Superset should now be ready!"
echo "Access: http://localhost:8088"
echo "Username: admin"
echo "Password: admin"
echo "=========================================="
