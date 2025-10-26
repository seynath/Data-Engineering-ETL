# Healthcare ETL Pipeline - Complete Startup Guide

## 🚀 Quick Start (5 Minutes)

Follow these steps to get Airflow, Superset, and the entire ETL pipeline running.

---

## Step 1: Verify Prerequisites

### Check Docker Installation

```bash
docker --version
docker-compose --version
```

**Expected output:**
```
Docker version 20.x.x or higher
Docker Compose version 2.x.x or higher
```

### Check Docker is Running

```bash
docker ps
```

If you see an error, start Docker Desktop first.

### Check Available Resources

```bash
docker system df
```

**Requirements:**
- At least 4GB RAM available
- At least 10GB free disk space

---

## Step 2: Prepare Environment

### Create .env File

```bash
# Copy the example environment file
cp .env.example .env
```

**Optional:** Edit `.env` to customize settings:
```bash
nano .env  # or use your preferred editor
```

### Create Required Directories

```bash
# Create all necessary directories
mkdir -p airflow/{dags,logs,plugins}
mkdir -p data/{bronze,silver}
mkdir -p logs/alerts
```

### Verify Dataset Files

Make sure you have the 9 required CSV files in the `dataset/` directory:

```bash
ls -lh dataset/
```

**Required files:**
- patients.csv
- encounters.csv
- diagnoses.csv
- procedures.csv
- medications.csv
- lab_tests.csv
- claims_and_billing.csv
- providers.csv
- denials.csv

---

## Step 3: Start Docker Services

### Option A: Automated Setup (Recommended)

```bash
./setup.sh
```

This script will:
1. Create `.env` file
2. Create directories
3. Start all Docker containers
4. Initialize databases
5. Set up the warehouse schema

**Time:** 3-5 minutes

### Option B: Manual Setup

```bash
# Start all services
docker-compose up -d

# Wait for services to be healthy (2-3 minutes)
watch docker-compose ps
```

Press `Ctrl+C` to exit the watch command once all services show "healthy" status.

---

## Step 4: Verify Services are Running

### Check Container Status

```bash
docker-compose ps
```

**Expected output:**
```
NAME                                  STATUS
healthcare-etl-airflow-init           Exited (0)
healthcare-etl-airflow-scheduler      Up (healthy)
healthcare-etl-airflow-webserver      Up (healthy)
healthcare-etl-postgres               Up (healthy)
healthcare-etl-superset               Up (healthy)
healthcare-etl-warehouse-db           Up (healthy)
```

All services should show "Up (healthy)" except `airflow-init` which should be "Exited (0)".

### Check Service Logs

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f airflow-webserver
docker-compose logs -f superset
```

Press `Ctrl+C` to exit log viewing.

---

## Step 5: Access the Applications

### 🌐 Airflow Web UI

**URL:** http://localhost:8080

**Credentials:**
- Username: `airflow`
- Password: `airflow`

**What you'll see:**
- DAGs list (should show `healthcare_etl_pipeline`)
- Pipeline execution history
- Task logs and monitoring

### 📊 Superset Dashboard

**URL:** http://localhost:8088

**Credentials:**
- Username: `admin`
- Password: `admin`

**What you'll see:**
- Dashboard list
- SQL Lab for queries
- Chart builder
- Dataset management

### 🗄️ PostgreSQL Database

**Connection Details:**
- Host: `localhost`
- Port: `5433` (warehouse) or `5432` (Airflow metadata)
- Database: `healthcare_warehouse`
- Username: `etl_user`
- Password: `etl_password`

**Connect via command line:**
```bash
docker-compose exec warehouse-db psql -U etl_user -d healthcare_warehouse
```

---

## Step 6: Run Your First Pipeline

### Method 1: Via Airflow UI (Recommended)

1. Open http://localhost:8080
2. Login with `airflow` / `airflow`
3. Find the `healthcare_etl_pipeline` DAG in the list
4. Click the toggle switch to **unpause** the DAG (if paused)
5. Click the **▶️ Play button** on the right
6. Select **"Trigger DAG"**
7. Click **"Trigger"** to confirm

### Method 2: Via Command Line

```bash
# Trigger the pipeline
docker-compose exec airflow-webserver airflow dags trigger healthcare_etl_pipeline

# Check the status
docker-compose exec airflow-webserver airflow dags list-runs -d healthcare_etl_pipeline
```

### Monitor Pipeline Execution

1. In Airflow UI, click on the DAG name `healthcare_etl_pipeline`
2. You'll see the DAG graph with all tasks
3. Watch tasks turn from white → yellow (running) → green (success)

**Pipeline Stages:**
1. **Bronze Ingestion** (~1-2 min) - Ingest CSV files
2. **Silver Transformation** (~2-3 min) - Clean and transform data
3. **Load to PostgreSQL** (~1-2 min) - Load Silver data to warehouse
4. **dbt Transformations** (~3-5 min) - Create Gold layer tables
5. **Data Quality Checks** (~1-2 min) - Validate data quality

**Total Time:** ~10-15 minutes for full dataset

---

## Step 7: View Results

### Check Data in Database

```bash
# Connect to warehouse
docker-compose exec warehouse-db psql -U etl_user -d healthcare_warehouse

# Run queries
\dt staging.*     -- List staging tables
\dt dimensions.*  -- List dimension tables
\dt facts.*       -- List fact tables

-- Check row counts
SELECT COUNT(*) FROM dimensions.dim_patient;
SELECT COUNT(*) FROM dimensions.dim_provider;
SELECT COUNT(*) FROM facts.fact_encounter;

-- Sample data
SELECT * FROM dimensions.dim_patient LIMIT 5;

-- Exit
\q
```

### View Dashboards in Superset

1. Open http://localhost:8088
2. Login with `admin` / `admin`
3. Click **"Dashboards"** in the top menu
4. You should see pre-configured dashboards:
   - Operational Overview
   - Financial Analytics
   - Clinical Analytics

**Note:** If dashboards are not visible, you may need to create them manually using the SQL Lab and chart builder.

### Check Data Quality Reports

```bash
# View Great Expectations reports
open great_expectations/uncommitted/data_docs/local_site/index.html

# Or view in browser
# Navigate to: file:///path/to/project/great_expectations/uncommitted/data_docs/local_site/index.html
```

---

## Step 8: Explore the Pipeline

### View Pipeline Code

**Airflow DAG:**
```bash
cat airflow/dags/healthcare_etl_dag.py
```

**Bronze Ingestion:**
```bash
cat bronze_ingestion.py
```

**Silver Transformation:**
```bash
cat silver_transformation.py
```

**dbt Models:**
```bash
ls -la dbt_project/models/
```

### View Logs

**Application Logs:**
```bash
ls -la logs/
cat logs/pipeline.log
```

**Airflow Task Logs:**
- View in Airflow UI by clicking on a task → "Log"

**Data Quality Reports:**
```bash
cat logs/data_quality_report.json
```

---

## Common Commands Reference

### Service Management

```bash
# Start all services
docker-compose up -d

# Stop all services (keeps data)
docker-compose down

# Stop and remove all data (WARNING: destructive!)
docker-compose down -v

# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart airflow-scheduler

# View service status
docker-compose ps

# View logs (all services)
docker-compose logs -f

# View logs (specific service)
docker-compose logs -f airflow-webserver
```

### Pipeline Operations

```bash
# Trigger pipeline
docker-compose exec airflow-webserver airflow dags trigger healthcare_etl_pipeline

# List all DAGs
docker-compose exec airflow-webserver airflow dags list

# View DAG runs
docker-compose exec airflow-webserver airflow dags list-runs -d healthcare_etl_pipeline

# Pause DAG
docker-compose exec airflow-webserver airflow dags pause healthcare_etl_pipeline

# Unpause DAG
docker-compose exec airflow-webserver airflow dags unpause healthcare_etl_pipeline

# Clear failed tasks
docker-compose exec airflow-webserver airflow tasks clear healthcare_etl_pipeline
```

### Database Operations

```bash
# Connect to warehouse
docker-compose exec warehouse-db psql -U etl_user -d healthcare_warehouse

# Run SQL file
docker-compose exec -T warehouse-db psql -U etl_user -d healthcare_warehouse < query.sql

# Backup database
docker-compose exec warehouse-db pg_dump -U etl_user healthcare_warehouse > backup.sql

# Restore database
docker-compose exec -T warehouse-db psql -U etl_user healthcare_warehouse < backup.sql

# View database size
docker-compose exec warehouse-db psql -U etl_user -d healthcare_warehouse -c "SELECT pg_size_pretty(pg_database_size('healthcare_warehouse'));"
```

---

## Troubleshooting

### Services Won't Start

**Problem:** Containers fail to start or show unhealthy status

**Solutions:**

1. **Check Docker resources:**
   ```bash
   docker system df
   docker system prune  # Clean up unused resources
   ```

2. **Check logs:**
   ```bash
   docker-compose logs -f
   ```

3. **Restart services:**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

4. **Full reset (WARNING: deletes all data):**
   ```bash
   docker-compose down -v
   docker-compose up -d
   ```

### Can't Access Airflow UI

**Problem:** http://localhost:8080 not accessible

**Solutions:**

1. **Wait for services to be healthy (2-3 minutes):**
   ```bash
   docker-compose ps
   ```

2. **Check Airflow webserver logs:**
   ```bash
   docker-compose logs -f airflow-webserver
   ```

3. **Restart Airflow webserver:**
   ```bash
   docker-compose restart airflow-webserver
   ```

4. **Check port is not in use:**
   ```bash
   lsof -i :8080  # macOS/Linux
   netstat -ano | findstr :8080  # Windows
   ```

### Can't Access Superset

**Problem:** http://localhost:8088 not accessible

**Solutions:**

1. **Wait for Superset to initialize (can take 2-3 minutes):**
   ```bash
   docker-compose logs -f superset
   ```

2. **Restart Superset:**
   ```bash
   docker-compose restart superset
   ```

3. **Check Superset health:**
   ```bash
   curl http://localhost:8088/health
   ```

### Pipeline Fails

**Problem:** DAG execution fails

**Solutions:**

1. **Check task logs in Airflow UI:**
   - Click on failed task → "Log"

2. **Check data files exist:**
   ```bash
   ls -la dataset/
   ```

3. **Check database connection:**
   ```bash
   docker-compose exec warehouse-db psql -U etl_user -d healthcare_warehouse -c "SELECT 1;"
   ```

4. **View application logs:**
   ```bash
   cat logs/pipeline.log
   ```

5. **Clear and retry:**
   ```bash
   docker-compose exec airflow-webserver airflow tasks clear healthcare_etl_pipeline
   docker-compose exec airflow-webserver airflow dags trigger healthcare_etl_pipeline
   ```

### Database Connection Issues

**Problem:** Can't connect to PostgreSQL

**Solutions:**

1. **Check database is running:**
   ```bash
   docker-compose ps warehouse-db
   ```

2. **Check database logs:**
   ```bash
   docker-compose logs -f warehouse-db
   ```

3. **Test connection:**
   ```bash
   docker-compose exec warehouse-db psql -U etl_user -d healthcare_warehouse -c "SELECT version();"
   ```

4. **Restart database:**
   ```bash
   docker-compose restart warehouse-db
   ```

### Port Already in Use

**Problem:** Port 8080, 8088, or 5432/5433 already in use

**Solutions:**

1. **Find process using port:**
   ```bash
   lsof -i :8080  # macOS/Linux
   ```

2. **Stop conflicting service or change port in docker-compose.yml:**
   ```yaml
   ports:
     - "8081:8080"  # Change 8080 to 8081
   ```

3. **Restart services:**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

---

## Performance Optimization

### Increase Docker Resources

**Docker Desktop Settings:**
1. Open Docker Desktop
2. Go to Settings → Resources
3. Increase:
   - CPUs: 4+ cores
   - Memory: 6-8 GB
   - Disk: 20+ GB

### Reduce Dataset Size for Testing

```bash
# Create smaller test dataset (first 1000 rows)
head -1001 dataset/patients.csv > dataset/patients_test.csv
# Repeat for other files
```

### Monitor Resource Usage

```bash
# View container resource usage
docker stats

# View disk usage
docker system df
```

---

## Next Steps

### 1. Customize the Pipeline

- **Modify transformations:** Edit `silver_transformation.py`
- **Update dbt models:** Edit files in `dbt_project/models/`
- **Adjust scheduling:** Edit `airflow/dags/healthcare_etl_dag.py`
- **Configure alerts:** Update `.env` with email/Slack settings

### 2. Create Custom Dashboards

1. Open Superset (http://localhost:8088)
2. Go to **SQL Lab**
3. Write custom queries
4. Create visualizations
5. Add to dashboards

### 3. Set Up Monitoring

- Configure email alerts in `.env`
- Set up Slack notifications
- Monitor data quality reports
- Review pipeline logs regularly

### 4. Schedule Regular Runs

The DAG is configured to run daily. To change the schedule:

1. Edit `airflow/dags/healthcare_etl_dag.py`
2. Modify the `schedule_interval` parameter
3. Restart Airflow scheduler:
   ```bash
   docker-compose restart airflow-scheduler
   ```

---

## Clean Up

### Stop Services (Keep Data)

```bash
docker-compose down
```

### Remove All Data (Fresh Start)

```bash
# WARNING: This deletes all data!
docker-compose down -v
rm -rf data/ logs/ airflow/logs/
```

### Remove Docker Images

```bash
# Remove project images
docker-compose down --rmi all

# Clean up all unused Docker resources
docker system prune -a
```

---

## Quick Reference Card

| Task | Command |
|------|---------|
| Start services | `docker-compose up -d` |
| Stop services | `docker-compose down` |
| View status | `docker-compose ps` |
| View logs | `docker-compose logs -f` |
| Trigger pipeline | `docker-compose exec airflow-webserver airflow dags trigger healthcare_etl_pipeline` |
| Connect to DB | `docker-compose exec warehouse-db psql -U etl_user -d healthcare_warehouse` |
| Restart service | `docker-compose restart [service-name]` |

| Service | URL | Credentials |
|---------|-----|-------------|
| Airflow | http://localhost:8080 | airflow / airflow |
| Superset | http://localhost:8088 | admin / admin |
| PostgreSQL | localhost:5433 | etl_user / etl_password |

---

## Support

For issues or questions:
1. Check this guide's troubleshooting section
2. Review logs: `docker-compose logs -f`
3. Check Airflow task logs in the UI
4. Review `README.md` for detailed documentation

---

**Ready to start?** Run these commands:

```bash
# 1. Create environment file
cp .env.example .env

# 2. Start services
docker-compose up -d

# 3. Wait 2-3 minutes, then access:
# - Airflow: http://localhost:8080
# - Superset: http://localhost:8088
```

🎉 **Happy data engineering!**
