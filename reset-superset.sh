#!/bin/bash
echo "Resetting Superset admin user..."

# Exec into the Superset container and reset the admin user
docker exec healthcare-etl-superset bash -c "
superset fab reset-password admin --password admin
"

echo "Done! Try logging in with username: admin and password: admin"
