# Quick Start Guide

Get the Healthcare ETL Pipeline running in 5 minutes!

## Prerequisites

- Docker Desktop installed and running
- At least 4GB RAM available for Docker
- 10GB free disk space

## Setup (First Time)

### Option 1: Automated Setup (Recommended)

```bash
# Clone/navigate to project directory
cd healthcare-etl-pipeline

# Run setup script
./setup.sh
```

**That's it!** The script will:
- Create `.env` file
- Create required directories
- Start all Docker services
- Initialize databases
- Populate date dimension

**Time**: 3-5 minutes

### Option 2: Manual Setup

```bash
# 1. Create environment file
cp .env.example .env

# 2. Create directories
mkdir -p airflow/{dags,logs,plugins} data/{bronze,silver} logs/alerts

# 3. Start services
docker-compose up -d

# 4. Wait for services (2-3 minutes)
watch docker-compose ps

# 5. Initialize warehouse
bash init-scripts/setup-warehouse.sh
```

## Access Services

Once setup is complete:

| Service | URL | Credentials |
|---------|-----|-------------|
| **Airflow** | http://localhost:8080 | airflow / airflow |
| **Superset** | http://localhost:8088 | admin / admin |
| **PostgreSQL** | localhost:5433 | etl_user / etl_password |

## Run Your First Pipeline

### 1. Add Data

Place your CSV files in the `dataset/` directory:

```bash
# Example: Copy sample data
cp /path/to/your/csvs/*.csv dataset/
```

Required files:
- patients.csv
- encounters.csv
- diagnoses.csv
- procedures.csv
- medications.csv
- lab_tests.csv
- claims_and_billing.csv
- providers.csv
- denials.csv

### 2. Trigger Pipeline

**Option A: From Airflow UI**

1. Open http://localhost:8080
2. Find `healthcare_etl_pipeline` DAG
3. Click the play button (▶️) to trigger

**Option B: From Command Line**

```bash
docker-compose exec airflow-webserver airflow dags trigger healthcare_etl_pipeline
```

### 3. Monitor Progress

Watch the pipeline execution in Airflow UI:
- Green = Success
- Red = Failed
- Yellow = Running

**Expected runtime**: 10-15 minutes for ~126K rows

### 4. View Results

**Check Data in Database**:
```bash
docker-compose exec warehouse-db psql -U etl_user -d healthcare_warehouse

# Run queries
SELECT COUNT(*) FROM dim_patient;
SELECT COUNT(*) FROM fact_encounter;
```

**View Dashboards**:
1. Open http://localhost:8088
2. Navigate to Dashboards
3. View pre-built analytics dashboards

## Common Commands

### Service Management

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart

# View status
docker-compose ps

# View logs
docker-compose logs -f
```

### Pipeline Operations

```bash
# Trigger DAG
docker-compose exec airflow-webserver airflow dags trigger healthcare_etl_pipeline

# List DAGs
docker-compose exec airflow-webserver airflow dags list

# View DAG runs
docker-compose exec airflow-webserver airflow dags list-runs -d healthcare_etl_pipeline

# Pause DAG
docker-compose exec airflow-webserver airflow dags pause healthcare_etl_pipeline

# Unpause DAG
docker-compose exec airflow-webserver airflow dags unpause healthcare_etl_pipeline
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
```

### Troubleshooting

```bash
# Check service health
docker-compose ps

# View service logs
docker-compose logs -f [service-name]

# Restart specific service
docker-compose restart airflow-scheduler

# Full reset (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d
```

## Pipeline Stages

The ETL pipeline runs through these stages:

1. **Bronze Ingestion** (1-2 min)
   - Copy CSV files to Bronze layer
   - Generate metadata
   - Validate file presence

2. **Silver Transformation** (2-3 min)
   - Clean and standardize data
   - Convert to Parquet format
   - Run data quality checks

3. **Gold Layer (dbt)** (3-5 min)
   - Create staging models
   - Build dimension tables
   - Build fact tables
   - Run dbt tests

4. **Validation & Reporting** (1-2 min)
   - Final data quality checks
   - Generate reports
   - Refresh Superset cache

## Next Steps

### Customize the Pipeline

1. **Modify transformations**: Edit `silver_transformation.py`
2. **Update dbt models**: Edit files in `dbt_project/models/`
3. **Adjust scheduling**: Edit `airflow/dags/healthcare_etl_dag.py`
4. **Configure alerts**: Update `.env` with email/Slack settings

### Create Dashboards

1. Open Superset (http://localhost:8088)
2. Connect to warehouse database
3. Create datasets from tables
4. Build custom visualizations
5. Combine into dashboards

### Monitor Data Quality

1. View Great Expectations reports in `great_expectations/uncommitted/data_docs/`
2. Check data quality logs in `logs/data_quality_report.json`
3. Review alerts in `logs/alerts/`

## Getting Help

### Check Documentation

- **Full README**: `README.md`
- **Docker Setup**: `DOCKER_SETUP.md`
- **Troubleshooting**: See README.md "Troubleshooting" section

### Common Issues

**Services won't start**:
- Check Docker is running: `docker ps`
- Check available resources: `docker system df`
- View logs: `docker-compose logs`

**Pipeline fails**:
- Check Airflow logs in UI
- View task logs: Click on failed task → View Log
- Check data quality reports

**Can't access UI**:
- Wait 2-3 minutes after starting services
- Check service health: `docker-compose ps`
- Try restarting: `docker-compose restart [service-name]`

## Clean Up

### Stop Services (Keep Data)

```bash
docker-compose down
```

### Remove Everything (Including Data)

```bash
# WARNING: This deletes all data!
docker-compose down -v
```

### Remove Docker Images

```bash
# Remove project images
docker-compose down --rmi all

# Clean up unused images
docker image prune -a
```

## Performance Tips

- **Reduce dataset size** for testing (use first 1000 rows)
- **Increase Docker memory** to 6-8GB for better performance
- **Use SSD** for Docker storage
- **Close unused applications** to free up resources

## Support

For issues or questions:
1. Check logs: `docker-compose logs -f`
2. Review documentation in `README.md`
3. Check troubleshooting guide
4. Review task logs in Airflow UI

---

**Ready to go?** Run `./setup.sh` and start building your data pipeline! 🚀
