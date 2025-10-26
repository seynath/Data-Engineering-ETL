# Healthcare ETL Pipeline - Startup Checklist

## Pre-Flight Checks

### ✅ Prerequisites
- [ ] Docker installed and running
- [ ] Docker Compose installed
- [ ] Ports available: 8080, 8088, 5432, 5433
- [ ] At least 4GB RAM available for Docker
- [ ] 10GB free disk space

### ✅ Verify Prerequisites
```bash
# Check Docker
docker --version
docker ps

# Check Docker Compose
docker-compose --version

# Check ports (should return nothing if available)
lsof -i :8080
lsof -i :8088
lsof -i :5432
lsof -i :5433
```

## Startup Steps

### Step 1: Make Scripts Executable
```bash
chmod +x pipeline-cli.sh start.sh troubleshoot.sh
```
- [ ] Scripts are executable

### Step 2: Start the Pipeline
```bash
./pipeline-cli.sh start
```
- [ ] Command runs without errors
- [ ] Wait ~30 seconds for services to start

### Step 3: Verify Services
```bash
./pipeline-cli.sh status
```

Check that all services show "(healthy)":
- [ ] healthcare-etl-postgres - (healthy)
- [ ] healthcare-etl-warehouse-db - (healthy)
- [ ] healthcare-etl-airflow-webserver - (healthy)
- [ ] healthcare-etl-airflow-scheduler - (healthy)
- [ ] healthcare-etl-superset - (healthy)

### Step 4: Access Airflow
```bash
./pipeline-cli.sh airflow
# Or open: http://localhost:8080
```
- [ ] Airflow UI loads
- [ ] Can login with: airflow / airflow
- [ ] See `healthcare_etl_pipeline` DAG

### Step 5: Access Superset
```bash
./pipeline-cli.sh superset
# Or open: http://localhost:8088
```
- [ ] Superset UI loads
- [ ] Can login with: admin / admin

### Step 6: Trigger the Pipeline
In Airflow UI:
- [ ] Find `healthcare_etl_pipeline` DAG
- [ ] Toggle it ON (if paused)
- [ ] Click "Trigger DAG"
- [ ] Watch it run in Graph view

Or use CLI:
```bash
./pipeline-cli.sh trigger-dag
```

### Step 7: Verify Data Flow
- [ ] Bronze layer: Check `data/bronze/` for CSV files
- [ ] Silver layer: Check `data/silver/` for Parquet files
- [ ] Gold layer: Query warehouse database

```bash
./pipeline-cli.sh db-warehouse
```

Then in psql:
```sql
\dt  -- List tables
SELECT COUNT(*) FROM dim_patient;
SELECT COUNT(*) FROM fact_encounter;
```

## Troubleshooting Checklist

### If Services Don't Start
- [ ] Run diagnostics: `./pipeline-cli.sh troubleshoot`
- [ ] Check logs: `./pipeline-cli.sh logs`
- [ ] Try clean restart:
  ```bash
  ./pipeline-cli.sh clean  # Type 'yes'
  ./pipeline-cli.sh start
  ```

### If Ports Are In Use
- [ ] Check what's using the port: `lsof -i :8080`
- [ ] Kill the process or change port in `docker-compose.yml`

### If Airflow UI Won't Load
- [ ] Check container status: `docker ps`
- [ ] Check logs: `./pipeline-cli.sh logs airflow-webserver`
- [ ] Wait longer (can take 60s on first start)
- [ ] Restart: `docker-compose restart airflow-webserver`

### If DAG Fails
- [ ] Check task logs in Airflow UI
- [ ] Check application logs: `./pipeline-cli.sh logs airflow-scheduler`
- [ ] Verify source data exists in `dataset/`
- [ ] Check database connectivity: `./pipeline-cli.sh db-warehouse`

### If Database Connection Fails
- [ ] Verify containers are healthy: `./pipeline-cli.sh status`
- [ ] Check warehouse-db logs: `./pipeline-cli.sh logs warehouse-db`
- [ ] Test connection:
  ```bash
  docker exec healthcare-etl-warehouse-db pg_isready -U etl_user
  ```

## Success Criteria

### ✅ All Systems Go
- [ ] All 5 containers running and healthy
- [ ] Airflow UI accessible and responsive
- [ ] Superset UI accessible and responsive
- [ ] DAG can be triggered manually
- [ ] DAG runs successfully (all tasks green)
- [ ] Data appears in bronze layer
- [ ] Data appears in silver layer
- [ ] Data appears in warehouse tables
- [ ] No errors in logs

### ✅ Data Pipeline Working
- [ ] Source CSV files in `dataset/`
- [ ] Bronze data created in `data/bronze/YYYY-MM-DD/`
- [ ] Silver data created in `data/silver/YYYY-MM-DD/`
- [ ] Dimension tables populated in warehouse
- [ ] Fact tables populated in warehouse
- [ ] Data quality validations passing

## Daily Operations Checklist

### Morning Check
- [ ] Check DAG run status from previous night
- [ ] Review any failed tasks
- [ ] Check data quality report: `airflow/logs/data_quality_report.json`
- [ ] Verify latest data in warehouse

### Manual Trigger
- [ ] Open Airflow UI
- [ ] Trigger `healthcare_etl_pipeline`
- [ ] Monitor execution
- [ ] Verify completion

### End of Day
- [ ] Review execution logs
- [ ] Check for any alerts in `airflow/logs/alerts/`
- [ ] Verify data freshness in Superset dashboards

## Maintenance Checklist

### Weekly
- [ ] Review disk space: `docker system df`
- [ ] Clean old logs if needed
- [ ] Check for Docker updates
- [ ] Review pipeline performance metrics

### Monthly
- [ ] Clean old bronze/silver data if needed
- [ ] Review and optimize DAG schedules
- [ ] Update dependencies if needed
- [ ] Backup warehouse database

## Quick Commands Reference

```bash
# Start
./pipeline-cli.sh start

# Status
./pipeline-cli.sh status

# Logs
./pipeline-cli.sh logs

# Trigger
./pipeline-cli.sh trigger-dag

# Troubleshoot
./pipeline-cli.sh troubleshoot

# Stop
./pipeline-cli.sh stop

# Help
./pipeline-cli.sh help
```

## Need Help?

1. Check [`GETTING_STARTED.md`](GETTING_STARTED.md)
2. Review [`RUN_PIPELINE.md`](RUN_PIPELINE.md)
3. Run `./pipeline-cli.sh troubleshoot`
4. Check logs: `./pipeline-cli.sh logs`
5. Review [`FIXED_ISSUES.md`](FIXED_ISSUES.md)

---

**Ready to start?**
```bash
./pipeline-cli.sh start
```
