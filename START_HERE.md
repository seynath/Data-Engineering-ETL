# 🚀 START HERE - Healthcare ETL Pipeline

## Quick Start (2 Commands)

Open your **Terminal** and run:

```bash
cd /Users/seynaththenura/Downloads/Projects/ETL
./start_services.sh
```

That's it! The script will:
1. ✅ Check Docker is running
2. ✅ Create required directories
3. ✅ Start all services in the correct order
4. ✅ Wait for services to be ready
5. ✅ Display access URLs

**Total time:** ~2 minutes

---

## Access the Applications

Once the script completes, open these URLs in your browser:

### 🌐 Airflow (Pipeline Orchestration)
- **URL:** http://localhost:8080
- **Username:** `airflow`
- **Password:** `airflow`

### 📊 Superset (Dashboards)
- **URL:** http://localhost:8088
- **Username:** `admin`
- **Password:** `admin`

---

## Run Your First Pipeline

### Step 1: Open Airflow
Go to http://localhost:8080 and login

### Step 2: Find the DAG
Look for `healthcare_etl_pipeline` in the list

### Step 3: Trigger the Pipeline
1. Click the toggle to **unpause** the DAG (if it's paused)
2. Click the **▶️ Play button** on the right
3. Select **"Trigger DAG"**
4. Click **"Trigger"** to confirm

### Step 4: Watch it Run
- Click on the DAG name to see the graph view
- Watch tasks turn green as they complete
- Click on any task to view logs

**Expected runtime:** 10-15 minutes for full dataset

---

## What the Pipeline Does

1. **Bronze Layer** (1-2 min)
   - Ingests 9 CSV files
   - Creates metadata
   - Stores raw data

2. **Silver Layer** (2-3 min)
   - Cleans and transforms data
   - Converts to Parquet format
   - Removes duplicates

3. **Load to PostgreSQL** (1-2 min)
   - Loads Silver data to warehouse

4. **Gold Layer (dbt)** (3-5 min)
   - Creates staging tables
   - Builds dimension tables (patients, providers, etc.)
   - Builds fact tables (encounters, claims, etc.)

5. **Data Quality** (1-2 min)
   - Runs validation checks
   - Generates quality reports

---

## View Results

### Check Data in Database

```bash
# Connect to warehouse
docker-compose exec warehouse-db psql -U etl_user -d healthcare_warehouse

# List tables
\dt staging.*
\dt dimensions.*
\dt facts.*

# Check row counts
SELECT COUNT(*) FROM dimensions.dim_patient;
SELECT COUNT(*) FROM facts.fact_encounter;

# Exit
\q
```

### View Dashboards

1. Open http://localhost:8088
2. Login with `admin` / `admin`
3. Navigate to **Dashboards**
4. Explore the analytics

---

## Common Commands

```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f airflow-webserver

# Stop services (keeps data)
docker-compose down

# Stop and remove all data
docker-compose down -v

# Restart a service
docker-compose restart airflow-webserver

# Check service health
./check_status.sh
```

---

## Troubleshooting

### Services Won't Start

```bash
# Stop everything
docker-compose down

# Start again
./start_services.sh
```

### Can't Access Airflow

1. Wait 2-3 minutes after starting
2. Check logs: `docker-compose logs -f airflow-webserver`
3. Restart: `docker-compose restart airflow-webserver`

### Pipeline Fails

1. Click on the failed task in Airflow UI
2. Click "Log" to see error details
3. Check if CSV files exist: `ls -la dataset/`

### Need Fresh Start

```bash
# WARNING: Deletes all data!
docker-compose down -v
./start_services.sh
```

---

## File Structure

```
ETL/
├── dataset/              # Source CSV files (9 files)
├── data/
│   ├── bronze/          # Raw ingested data
│   └── silver/          # Cleaned Parquet files
├── airflow/
│   └── dags/            # Pipeline definitions
├── dbt_project/
│   └── models/          # dbt transformations
├── logs/                # Application logs
└── docker-compose.yml   # Service configuration
```

---

## Next Steps

### 1. Explore Airflow
- View DAG graph
- Check task logs
- Monitor execution history

### 2. Query the Data
- Connect to PostgreSQL
- Run SQL queries
- Explore dimension and fact tables

### 3. Create Dashboards
- Open Superset
- Use SQL Lab
- Build visualizations

### 4. Customize the Pipeline
- Edit `silver_transformation.py` for data transformations
- Modify `dbt_project/models/` for Gold layer logic
- Update `airflow/dags/healthcare_etl_dag.py` for scheduling

---

## Getting Help

1. **Check logs:** `docker-compose logs -f`
2. **Check status:** `./check_status.sh`
3. **Read docs:**
   - `HOW_TO_RUN.md` - Quick instructions
   - `STARTUP_GUIDE.md` - Detailed guide
   - `README.md` - Full documentation

---

## Summary

**To start:**
```bash
./start_services.sh
```

**To access:**
- Airflow: http://localhost:8080 (airflow/airflow)
- Superset: http://localhost:8088 (admin/admin)

**To run pipeline:**
1. Open Airflow
2. Trigger `healthcare_etl_pipeline` DAG
3. Watch it execute

**To stop:**
```bash
docker-compose down
```

---

🎉 **You're all set!** Run `./start_services.sh` to begin.
