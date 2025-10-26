# Getting Started - Healthcare ETL Pipeline

## 🚀 Fastest Way to Start

```bash
./pipeline-cli.sh start
```

That's it! The script handles everything automatically.

## 📋 What You Need

- Docker & Docker Compose installed
- Ports available: 8080 (Airflow), 8088 (Superset), 5432, 5433 (PostgreSQL)
- At least 4GB RAM available for Docker

## 🎯 Three Ways to Run

### Option 1: Use the CLI Helper (Easiest)
```bash
# Make executable (first time only)
chmod +x pipeline-cli.sh

# Start everything
./pipeline-cli.sh start

# Check status
./pipeline-cli.sh status

# View logs
./pipeline-cli.sh logs

# Trigger the ETL pipeline
./pipeline-cli.sh trigger-dag

# See all commands
./pipeline-cli.sh help
```

### Option 2: Use the Start Script
```bash
chmod +x start.sh
./start.sh
```

### Option 3: Manual Docker Compose
```bash
# Clean start
docker-compose down -v

# Start databases
docker-compose up -d postgres warehouse-db
sleep 15

# Initialize Airflow
docker-compose run --rm airflow-init

# Start all services
docker-compose up -d
```

## 🌐 Access Your Services

After starting (wait ~30 seconds for services to be ready):

| Service | URL | Username | Password |
|---------|-----|----------|----------|
| **Airflow** | http://localhost:8080 | airflow | airflow |
| **Superset** | http://localhost:8088 | admin | admin |

## ✅ Verify Everything Works

### 1. Check Service Status
```bash
./pipeline-cli.sh status
```

All services should show "(healthy)" status.

### 2. Open Airflow
```bash
./pipeline-cli.sh airflow
# Or manually: http://localhost:8080
```

### 3. Trigger the Pipeline
In Airflow UI:
- Find `healthcare_etl_pipeline` DAG
- Toggle it ON (if paused)
- Click "Trigger DAG" button

Or use CLI:
```bash
./pipeline-cli.sh trigger-dag
```

### 4. Monitor Progress
Watch the DAG run in Airflow's Graph or Grid view.

## 🔧 Common Commands

```bash
# Start
./pipeline-cli.sh start

# Stop (keep data)
./pipeline-cli.sh stop

# Restart
./pipeline-cli.sh restart

# Clean everything (removes data)
./pipeline-cli.sh clean

# Check status
./pipeline-cli.sh status

# View logs
./pipeline-cli.sh logs
./pipeline-cli.sh logs airflow-scheduler

# Troubleshoot
./pipeline-cli.sh troubleshoot

# Open UIs
./pipeline-cli.sh airflow
./pipeline-cli.sh superset

# Database access
./pipeline-cli.sh db-warehouse
./pipeline-cli.sh db-airflow
```

## 🐛 Something Wrong?

### Quick Fix
```bash
# Stop everything
./pipeline-cli.sh stop

# Clean start
./pipeline-cli.sh clean  # Type 'yes' when prompted

# Start fresh
./pipeline-cli.sh start
```

### Run Diagnostics
```bash
./pipeline-cli.sh troubleshoot
```

### Check Logs
```bash
# All services
./pipeline-cli.sh logs

# Specific service
./pipeline-cli.sh logs airflow-webserver
./pipeline-cli.sh logs warehouse-db
```

## 📊 Pipeline Flow

```
Source CSV Files (dataset/)
    ↓
Bronze Layer (data/bronze/) - Raw ingestion
    ↓
Data Quality Validation (Great Expectations)
    ↓
Silver Layer (data/silver/) - Cleaned & transformed
    ↓
Load to PostgreSQL Warehouse
    ↓
Gold Layer (dbt) - Dimensional models
    ↓
Superset Dashboards
```

## 📁 Important Directories

- `dataset/` - Source CSV files
- `data/bronze/` - Raw ingested data
- `data/silver/` - Transformed data
- `airflow/dags/` - Airflow DAG definitions
- `airflow/logs/` - Execution logs
- `dbt_project/` - dbt models for gold layer
- `config/` - Pipeline configuration files

## 🎓 Next Steps

1. **Explore Airflow**: http://localhost:8080
   - View DAG structure
   - Check task logs
   - Monitor execution history

2. **Check Data Quality Reports**:
   - Look in `airflow/logs/data_quality_report.json`
   - Review Great Expectations validation results

3. **Query the Warehouse**:
   ```bash
   ./pipeline-cli.sh db-warehouse
   ```
   Then run SQL:
   ```sql
   \dt  -- List tables
   SELECT * FROM dim_patient LIMIT 5;
   SELECT * FROM fact_encounter LIMIT 5;
   ```

4. **Create Dashboards in Superset**: http://localhost:8088
   - Connect to the warehouse database
   - Create charts and dashboards

## 📚 More Documentation

- `RUN_PIPELINE.md` - Detailed running instructions
- `README.md` - Project overview
- `QUICK_START.md` - Quick reference guide
- `airflow/dags/README.md` - DAG documentation
- `dbt_project/README.md` - dbt documentation

## 💡 Tips

- The pipeline runs daily at 2 AM UTC by default
- You can trigger it manually anytime from Airflow UI
- Check logs if a task fails: `./pipeline-cli.sh logs`
- Use `./pipeline-cli.sh troubleshoot` for diagnostics
- Data persists in Docker volumes even after stopping

## 🆘 Need Help?

1. Run troubleshooting: `./pipeline-cli.sh troubleshoot`
2. Check logs: `./pipeline-cli.sh logs [service-name]`
3. Review error messages in Airflow UI
4. Try a clean restart: `./pipeline-cli.sh clean` then `./pipeline-cli.sh start`

---

**Ready to go? Run this:**
```bash
./pipeline-cli.sh start
```
