# How to Run the Healthcare ETL Pipeline

## 🚨 Important: Run These Commands in Your Terminal

The Docker Compose startup is a long-running process. Please run these commands **in your terminal** (not through the IDE).

---

## Step-by-Step Instructions

### 1. Open Your Terminal

Open Terminal app on macOS or your preferred terminal emulator.

### 2. Navigate to Project Directory

```bash
cd /Users/seynaththenura/Downloads/Projects/ETL
```

### 3. Start Docker Services

```bash
docker-compose up -d
```

**Wait 2-3 minutes** for all services to start and become healthy.

### 4. Check Service Status

```bash
docker-compose ps
```

**Expected output:** All services should show "Up (healthy)" status:
- healthcare-etl-postgres
- healthcare-etl-warehouse-db
- healthcare-etl-superset
- healthcare-etl-airflow-webserver
- healthcare-etl-airflow-scheduler

### 5. View Logs (Optional)

```bash
# View all logs
docker-compose logs -f

# Or view specific service
docker-compose logs -f airflow-webserver
```

Press `Ctrl+C` to exit log viewing.

---

## Access the Applications

Once all services are running (check with `docker-compose ps`):

### 🌐 Airflow Web UI
- **URL:** http://localhost:8080
- **Username:** `airflow`
- **Password:** `airflow`

### 📊 Superset Dashboard
- **URL:** http://localhost:8088
- **Username:** `admin`
- **Password:** `admin`

### 🗄️ PostgreSQL Database
```bash
# Connect to warehouse database
docker-compose exec warehouse-db psql -U etl_user -d healthcare_warehouse
```

---

## Run the ETL Pipeline

### Option 1: Via Airflow UI (Recommended)

1. Open http://localhost:8080 in your browser
2. Login with `airflow` / `airflow`
3. Find `healthcare_etl_pipeline` in the DAGs list
4. Click the toggle to **unpause** the DAG (if paused)
5. Click the **▶️ Play button** → **Trigger DAG**
6. Watch the pipeline execute in the Graph view

### Option 2: Via Command Line

```bash
# Trigger the pipeline
docker-compose exec airflow-webserver airflow dags trigger healthcare_etl_pipeline

# Check status
docker-compose exec airflow-webserver airflow dags list-runs -d healthcare_etl_pipeline
```

---

## Troubleshooting

### Services Won't Start

If `docker-compose ps` shows unhealthy services:

```bash
# Stop all services
docker-compose down

# Start again
docker-compose up -d

# Wait 2-3 minutes and check status
docker-compose ps
```

### Airflow Init Fails

If you see "airflow-init didn't complete successfully":

```bash
# Remove volumes and start fresh
docker-compose down -v
docker-compose up -d
```

### Can't Access Web UIs

1. **Wait 2-3 minutes** after starting services
2. Check service health: `docker-compose ps`
3. Check logs: `docker-compose logs -f airflow-webserver`
4. Try restarting: `docker-compose restart airflow-webserver`

### Port Already in Use

If you get "port already in use" errors:

```bash
# Check what's using the port
lsof -i :8080  # For Airflow
lsof -i :8088  # For Superset

# Kill the process or change ports in docker-compose.yml
```

---

## Quick Commands Reference

```bash
# Start services
docker-compose up -d

# Stop services (keeps data)
docker-compose down

# Stop and remove all data
docker-compose down -v

# View status
docker-compose ps

# View logs
docker-compose logs -f

# Restart a service
docker-compose restart airflow-webserver

# Trigger pipeline
docker-compose exec airflow-webserver airflow dags trigger healthcare_etl_pipeline

# Connect to database
docker-compose exec warehouse-db psql -U etl_user -d healthcare_warehouse
```

---

## What to Expect

### First Time Startup (5-10 minutes)

1. **Docker pulls images** (2-3 minutes)
   - PostgreSQL, Airflow, Superset images

2. **Services initialize** (2-3 minutes)
   - Databases create schemas
   - Airflow installs Python packages
   - Superset initializes

3. **Services become healthy** (1-2 minutes)
   - Health checks pass
   - Web UIs become accessible

### Pipeline Execution (10-15 minutes)

1. **Bronze Ingestion** (~1-2 min)
   - Copies CSV files to Bronze layer
   - Generates metadata

2. **Silver Transformation** (~2-3 min)
   - Cleans and transforms data
   - Creates Parquet files

3. **Load to PostgreSQL** (~1-2 min)
   - Loads Silver data to warehouse

4. **dbt Transformations** (~3-5 min)
   - Creates staging tables
   - Builds dimension tables
   - Builds fact tables

5. **Data Quality Checks** (~1-2 min)
   - Runs Great Expectations validations

---

## Next Steps After Startup

### 1. Verify Data

```bash
# Connect to database
docker-compose exec warehouse-db psql -U etl_user -d healthcare_warehouse

# Check tables
\dt staging.*
\dt dimensions.*
\dt facts.*

# Check row counts
SELECT COUNT(*) FROM dimensions.dim_patient;
SELECT COUNT(*) FROM facts.fact_encounter;

# Exit
\q
```

### 2. View Dashboards

1. Open http://localhost:8088
2. Login with `admin` / `admin`
3. Navigate to **Dashboards**
4. Explore pre-built analytics

### 3. Monitor Pipeline

1. Open http://localhost:8080
2. Click on `healthcare_etl_pipeline` DAG
3. View **Graph** to see task dependencies
4. Click on tasks to view logs

---

## Common Issues and Solutions

### Issue: "Cannot connect to Docker daemon"
**Solution:** Start Docker Desktop application

### Issue: "Port 8080 already in use"
**Solution:** 
```bash
# Find and kill the process
lsof -i :8080
kill -9 <PID>

# Or change port in docker-compose.yml
```

### Issue: "Airflow webserver not accessible"
**Solution:**
```bash
# Wait 2-3 minutes after starting
# Check logs
docker-compose logs -f airflow-webserver

# Restart if needed
docker-compose restart airflow-webserver
```

### Issue: "Pipeline fails immediately"
**Solution:**
```bash
# Check if CSV files exist
ls -la dataset/

# Check Airflow logs in UI
# Click on failed task → View Log
```

---

## Clean Up

### Stop Services (Keep Data)
```bash
docker-compose down
```

### Remove Everything (Fresh Start)
```bash
# WARNING: Deletes all data!
docker-compose down -v
rm -rf data/ logs/ airflow/logs/
```

---

## Need Help?

1. Check service logs: `docker-compose logs -f`
2. Check service status: `docker-compose ps`
3. Review `STARTUP_GUIDE.md` for detailed troubleshooting
4. Check `README.md` for full documentation

---

## Summary

**To start the application:**

```bash
# In your terminal
cd /Users/seynaththenura/Downloads/Projects/ETL
docker-compose up -d

# Wait 2-3 minutes, then access:
# Airflow: http://localhost:8080 (airflow/airflow)
# Superset: http://localhost:8088 (admin/admin)
```

**To run the pipeline:**
1. Open http://localhost:8080
2. Find `healthcare_etl_pipeline` DAG
3. Click play button → Trigger DAG

🎉 **That's it!** Your ETL pipeline is now running.
