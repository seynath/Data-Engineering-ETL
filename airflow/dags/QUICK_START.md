# Healthcare ETL Pipeline - Quick Start Guide

## Prerequisites

1. **Airflow Environment**: Apache Airflow 2.8+ installed and running
2. **Python Dependencies**: All required packages installed (see requirements.txt)
3. **PostgreSQL Database**: Healthcare warehouse database created
4. **Source Data**: 9 CSV files in the source directory
5. **dbt Project**: dbt models configured and tested

## Setup Steps

### 1. Deploy the DAG

Copy the DAG file to your Airflow dags folder:

```bash
# If using Docker Compose
cp airflow/dags/healthcare_etl_dag.py /path/to/airflow/dags/

# Or if using mounted volumes
# The file should already be in the correct location
```

### 2. Verify Environment Variables

Ensure these variables are set in your `.env` file or Airflow environment:

```bash
# File Paths
BRONZE_DATA_PATH=/opt/airflow/data/bronze
SILVER_DATA_PATH=/opt/airflow/data/silver
SOURCE_CSV_PATH=/opt/airflow/dataset
SILVER_CONFIG_PATH=/opt/airflow/config/silver_table_config.yaml

# Database
POSTGRES_HOST=warehouse-db
POSTGRES_PORT=5432
POSTGRES_DB=healthcare_warehouse
POSTGRES_USER=etl_user
POSTGRES_PASSWORD=etl_password

# Alerting
ALERT_EMAIL=data-team@hospital.com
```

### 3. Check DAG is Loaded

```bash
# List all DAGs
airflow dags list | grep healthcare_etl_pipeline

# Check for parsing errors
airflow dags list-import-errors
```

Expected output:
```
healthcare_etl_pipeline
```

### 4. Verify DAG Structure

```bash
# Show DAG structure
airflow dags show healthcare_etl_pipeline

# Or view in Airflow UI
# Navigate to: http://localhost:8080/dags/healthcare_etl_pipeline/graph
```

## Running the Pipeline

### Option 1: Manual Trigger (Recommended for First Run)

#### Via Airflow UI:
1. Open Airflow UI: `http://localhost:8080`
2. Find `healthcare_etl_pipeline` in the DAGs list
3. Toggle the DAG to "On" (if not already)
4. Click the "Play" button (▶) to trigger manually
5. Monitor progress in the Graph or Tree view

#### Via CLI:
```bash
# Trigger the DAG
airflow dags trigger healthcare_etl_pipeline

# Check the run status
airflow dags list-runs -d healthcare_etl_pipeline

# View task status
airflow tasks list healthcare_etl_pipeline
```

### Option 2: Scheduled Run

The DAG runs automatically daily at 2:00 AM UTC. Just ensure:
1. DAG is toggled "On" in the UI
2. Airflow scheduler is running
3. Source CSV files are available

### Option 3: Test Individual Tasks

Test tasks without running the full DAG:

```bash
# Test validate_source_files
airflow tasks test healthcare_etl_pipeline validate_source_files 2025-01-15

# Test ingest_bronze_layer
airflow tasks test healthcare_etl_pipeline ingest_bronze_layer 2025-01-15

# Test a Silver transformation
airflow tasks test healthcare_etl_pipeline silver_transformations.transform_patients 2025-01-15

# Test dbt staging
airflow tasks test healthcare_etl_pipeline dbt_gold_layer.dbt_run_staging 2025-01-15
```

## Monitoring

### Real-Time Monitoring

1. **Airflow UI - Graph View**:
   - Shows task status with color coding
   - Green: Success
   - Red: Failed
   - Yellow: Running
   - Light blue: Queued

2. **Airflow UI - Gantt Chart**:
   - Shows task execution timeline
   - Identifies bottlenecks

3. **Task Logs**:
   - Click on any task → "Log" button
   - View detailed execution logs

### Post-Run Monitoring

1. **Data Quality Report**:
   ```bash
   cat /opt/airflow/logs/data_quality_report.json
   ```

2. **Alert Files** (if failures occurred):
   ```bash
   ls -la /opt/airflow/logs/alerts/
   cat /opt/airflow/logs/alerts/alert_*.json
   ```

3. **Great Expectations Reports**:
   ```bash
   # Open in browser
   open /opt/airflow/great_expectations/uncommitted/data_docs/local_site/index.html
   ```

## Troubleshooting

### Issue: DAG Not Appearing

**Symptoms**: DAG not visible in Airflow UI

**Solutions**:
```bash
# Check for import errors
airflow dags list-import-errors

# Verify file is in dags folder
ls -la $AIRFLOW_HOME/dags/healthcare_etl_dag.py

# Restart Airflow webserver and scheduler
docker-compose restart airflow-webserver airflow-scheduler
```

### Issue: Task Stuck in "Running"

**Symptoms**: Task shows as running but no progress

**Solutions**:
```bash
# Check task logs for errors
airflow tasks logs healthcare_etl_pipeline <task_id> 2025-01-15

# Clear task state and retry
airflow tasks clear healthcare_etl_pipeline -t <task_id> -s 2025-01-15 -e 2025-01-15

# Check if task timeout is too short
# Edit timeout in DAG file if needed
```

### Issue: "No module named 'bronze_ingestion'"

**Symptoms**: Import error in DAG

**Solutions**:
```bash
# Verify Python modules are in correct location
ls -la /opt/airflow/bronze_ingestion.py
ls -la /opt/airflow/silver_transformation.py
ls -la /opt/airflow/data_quality.py

# Check PYTHONPATH
echo $PYTHONPATH

# Restart Airflow to reload modules
docker-compose restart
```

### Issue: Database Connection Error

**Symptoms**: dbt tasks or Gold validation fails

**Solutions**:
```bash
# Test database connection
psql -h warehouse-db -U etl_user -d healthcare_warehouse

# Verify environment variables
env | grep POSTGRES

# Check database is running
docker-compose ps warehouse-db

# Test from Python
python -c "import psycopg2; conn = psycopg2.connect(host='warehouse-db', port=5432, database='healthcare_warehouse', user='etl_user', password='etl_password'); print('✓ Connected')"
```

### Issue: Great Expectations Validation Fails

**Symptoms**: validate_silver_layer task fails

**Solutions**:
```bash
# View validation results
cat /opt/airflow/logs/alerts/alert_*.json

# Run validation manually
python data_quality.py --layer silver --date 2025-01-15

# Check expectation suites
ls -la /opt/airflow/great_expectations/expectations/

# Review data docs
open /opt/airflow/great_expectations/uncommitted/data_docs/local_site/index.html
```

### Issue: dbt Tests Fail

**Symptoms**: dbt_test_staging or dbt_test_gold fails

**Solutions**:
```bash
# Run dbt tests manually
cd /opt/airflow/dbt_project
dbt test --profiles-dir . --select staging.*

# View test results
dbt test --profiles-dir . --store-failures

# Check specific test
dbt test --profiles-dir . --select <test_name>

# Debug with dbt logs
cat /opt/airflow/dbt_project/logs/dbt.log
```

## Performance Optimization

### If Pipeline Takes Too Long

1. **Check Parallel Execution**:
   - Verify Silver transformations run in parallel
   - Increase Airflow parallelism settings if needed

2. **Optimize dbt Models**:
   ```bash
   # Use incremental materialization
   # Add indexes to frequently joined columns
   # Partition large tables
   ```

3. **Increase Task Timeouts**:
   - Edit timeout values in DAG file
   - Restart Airflow to apply changes

4. **Monitor Resource Usage**:
   ```bash
   # Check CPU and memory
   docker stats
   
   # Check disk I/O
   iostat -x 1
   ```

## Validation Checklist

After first successful run, verify:

- [ ] All 9 Bronze CSV files created with timestamps
- [ ] Bronze metadata.json file generated
- [ ] All 9 Silver Parquet files created
- [ ] Silver validation passed (check data quality report)
- [ ] All dimension tables populated (6 tables)
- [ ] All fact tables populated (4 tables)
- [ ] dbt tests passed (check logs)
- [ ] Data quality report generated
- [ ] No error alerts in logs/alerts/

## Next Steps

1. **Set Up Monitoring**:
   - Configure external monitoring (Datadog, Prometheus)
   - Set up dashboard for pipeline metrics

2. **Configure Email Alerts**:
   - Set up SMTP server in Airflow
   - Test email notifications

3. **Implement Superset Integration**:
   - Add Superset API calls to refresh_superset_cache()
   - Configure dashboard auto-refresh

4. **Schedule Regular Maintenance**:
   - Archive old Bronze/Silver data
   - Vacuum PostgreSQL database
   - Review and update expectation suites

5. **Document Runbook**:
   - Create operations runbook for on-call team
   - Document escalation procedures
   - Add contact information

## Support

For issues or questions:
- **Logs**: `/opt/airflow/logs/`
- **Data Quality Reports**: `/opt/airflow/logs/data_quality_report.json`
- **Alerts**: `/opt/airflow/logs/alerts/`
- **Email**: data-team@hospital.com

## Useful Commands Reference

```bash
# DAG Management
airflow dags list
airflow dags trigger healthcare_etl_pipeline
airflow dags pause healthcare_etl_pipeline
airflow dags unpause healthcare_etl_pipeline

# Task Management
airflow tasks list healthcare_etl_pipeline
airflow tasks test healthcare_etl_pipeline <task_id> <date>
airflow tasks clear healthcare_etl_pipeline -t <task_id>

# Run Management
airflow dags list-runs -d healthcare_etl_pipeline
airflow dags delete healthcare_etl_pipeline  # Careful!

# Logs
airflow tasks logs healthcare_etl_pipeline <task_id> <date>

# Database
psql -h warehouse-db -U etl_user -d healthcare_warehouse

# dbt
cd /opt/airflow/dbt_project
dbt run --profiles-dir .
dbt test --profiles-dir .
dbt docs generate --profiles-dir .

# Great Expectations
python data_quality.py --layer both --date 2025-01-15
```

## Success Indicators

A successful pipeline run should show:
- ✅ All tasks green in Airflow UI
- ✅ Data quality report with 100% success rate
- ✅ No alert files in logs/alerts/
- ✅ All Gold layer tables populated
- ✅ Superset dashboards updated
- ✅ Success email received (if configured)

Happy data engineering! 🚀
