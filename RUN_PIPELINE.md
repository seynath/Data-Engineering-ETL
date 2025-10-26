# How to Run the Healthcare ETL Pipeline

## Quick Start (Recommended)

```bash
# Make the script executable (first time only)
chmod +x start.sh

# Start everything
./start.sh
```

This script will:
1. Clean up any existing containers
2. Start databases first
3. Initialize Airflow properly
4. Start all services
5. Show you the access URLs

## Manual Step-by-Step

If you prefer to run commands manually:

### 1. Clean Up (if needed)
```bash
docker-compose down -v
```

### 2. Start Databases First
```bash
docker-compose up -d postgres warehouse-db
```

Wait 15-20 seconds for databases to initialize.

### 3. Initialize Airflow
```bash
docker-compose run --rm airflow-init
```

### 4. Start All Services
```bash
docker-compose up -d
```

### 5. Check Status
```bash
docker-compose ps
```

## Access the Services

Once everything is running:

- **Airflow UI**: http://localhost:8080
  - Username: `airflow`
  - Password: `airflow`

- **Superset UI**: http://localhost:8088
  - Username: `admin`
  - Password: `admin`

- **PostgreSQL (Airflow Metadata)**: `localhost:5432`
  - Database: `airflow`
  - User: `airflow`
  - Password: `airflow`

- **PostgreSQL (Data Warehouse)**: `localhost:5433`
  - Database: `healthcare_warehouse`
  - User: `etl_user`
  - Password: `etl_password`

## Running the ETL Pipeline

1. Open Airflow UI at http://localhost:8080
2. Find the `healthcare_etl_pipeline` DAG
3. Toggle it ON (if paused)
4. Click "Trigger DAG" to run manually
5. Monitor progress in the Graph or Grid view

## Troubleshooting

### Run Diagnostics
```bash
chmod +x troubleshoot.sh
./troubleshoot.sh
```

### Common Issues

#### 1. "airflow-init is unhealthy"
This happens when the init script runs in the wrong container.

**Solution:**
```bash
docker-compose down -v
./start.sh
```

#### 2. Port Already in Use
**Check which process is using the port:**
```bash
# For port 8080 (Airflow)
lsof -i :8080

# For port 5432 (Postgres)
lsof -i :5432

# For port 8088 (Superset)
lsof -i :8088
```

**Solution:** Kill the process or change the port in `docker-compose.yml`

#### 3. Permission Errors
```bash
sudo chown -R $USER:0 airflow/
sudo chown -R $USER:0 data/
```

#### 4. Services Not Starting
**View logs:**
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f airflow-webserver
docker-compose logs -f warehouse-db
```

#### 5. Database Connection Issues
**Test database connectivity:**
```bash
# Test Airflow DB
docker exec -it healthcare-etl-postgres psql -U airflow -d airflow -c "SELECT 1;"

# Test Warehouse DB
docker exec -it healthcare-etl-warehouse-db psql -U etl_user -d healthcare_warehouse -c "SELECT 1;"
```

## Stopping the Pipeline

### Stop All Services (Keep Data)
```bash
docker-compose down
```

### Stop and Remove All Data
```bash
docker-compose down -v
```

### Stop Specific Service
```bash
docker-compose stop airflow-webserver
```

## Viewing Logs

### All Services
```bash
docker-compose logs -f
```

### Specific Service
```bash
docker-compose logs -f airflow-scheduler
docker-compose logs -f warehouse-db
```

### Last N Lines
```bash
docker-compose logs --tail=100 airflow-webserver
```

## Restarting Services

### Restart All
```bash
docker-compose restart
```

### Restart Specific Service
```bash
docker-compose restart airflow-scheduler
```

## Environment Variables

You can customize the setup by creating a `.env` file:

```bash
# Database Configuration
POSTGRES_USER=etl_user
POSTGRES_PASSWORD=etl_password
POSTGRES_DB=healthcare_warehouse
POSTGRES_HOST=warehouse-db
POSTGRES_PORT=5432

# Airflow Configuration
_AIRFLOW_WWW_USER_USERNAME=airflow
_AIRFLOW_WWW_USER_PASSWORD=airflow
AIRFLOW_UID=50000

# Superset Configuration
SUPERSET_SECRET_KEY=your_secret_key_here

# Data Paths
BRONZE_DATA_PATH=/opt/airflow/data/bronze
SILVER_DATA_PATH=/opt/airflow/data/silver
SOURCE_CSV_PATH=/opt/airflow/dataset

# Alerts
ALERT_EMAIL=data-team@hospital.com
ENVIRONMENT=development
```

## Health Checks

All services have health checks configured. Check their status:

```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
```

Healthy services will show "(healthy)" in their status.

## Next Steps

After the pipeline is running:

1. **Verify Data Ingestion**: Check that CSV files are being processed
2. **Monitor DAG Runs**: Watch the Airflow UI for task execution
3. **Check Data Quality**: Review Great Expectations validation results
4. **Explore Data**: Use Superset to create dashboards
5. **Review Logs**: Check `airflow/logs/` for detailed execution logs

## Getting Help

If you encounter issues:

1. Run `./troubleshoot.sh` for diagnostics
2. Check logs: `docker-compose logs -f [service-name]`
3. Verify all containers are healthy: `docker ps`
4. Review the error messages in the Airflow UI
