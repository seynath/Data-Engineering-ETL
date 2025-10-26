# Healthcare ETL Pipeline DAG

## Overview

The `healthcare_etl_dag.py` implements a complete ETL pipeline for hospital operational data using Apache Airflow orchestration with the medallion architecture (Bronze/Silver/Gold layers).

## DAG Configuration

- **DAG ID**: `healthcare_etl_pipeline`
- **Schedule**: Daily at 2:00 AM UTC (`0 2 * * *`)
- **Start Date**: January 1, 2025
- **Catchup**: Disabled (only runs for current dates)
- **Max Active Runs**: 1 (prevents concurrent executions)
- **DAG Timeout**: 2 hours

## Pipeline Stages

### 1. Bronze Layer (Raw Data Ingestion)
- **validate_source_files**: Validates all 9 CSV files are present
- **ingest_bronze_layer**: Copies CSV files to Bronze with metadata
- **validate_bronze_layer**: Validates row counts

**Timeout**: 5-10 minutes per task

### 2. Silver Layer (Data Cleaning)
- **silver_transformations** (Task Group):
  - `transform_patients`
  - `transform_encounters`
  - `transform_diagnoses`
  - `transform_procedures`
  - `transform_medications`
  - `transform_lab_tests`
  - `transform_claims_and_billing`
  - `transform_providers`
  - `transform_denials`
- **validate_silver_layer**: Great Expectations validation

**Timeout**: 15 minutes per transformation, 20 minutes for validation

### 3. Gold Layer (dbt Transformations)
- **dbt_gold_layer** (Task Group):
  - `dbt_run_staging`: Run staging models
  - `dbt_test_staging`: Test staging models
  - `dbt_run_dimensions`: Run dimension models
  - `dbt_run_facts`: Run fact models
  - `dbt_test_gold`: Test all Gold layer models

**Timeout**: 10-20 minutes per task

### 4. Data Quality & Reporting
- **validate_gold_layer**: Validate Gold layer tables
- **generate_data_quality_report**: Generate comprehensive report
- **refresh_superset_cache**: Refresh Superset dashboards

**Timeout**: 5-10 minutes per task

## Retry Configuration

- **Retries**: 3 attempts
- **Initial Retry Delay**: 5 minutes
- **Exponential Backoff**: Enabled
- **Max Retry Delay**: 30 minutes

## Alerting

### Email Alerts

The DAG sends email alerts for:
- **Task Failures**: Detailed error information with logs link
- **DAG Success**: Summary of completed pipeline (optional)

Alert recipients are configured via the `ALERT_EMAIL` environment variable.

### Alert Content

**Failure Alerts Include**:
- DAG and task identification
- Execution date and try number
- Error details and stack trace
- Links to task logs
- Troubleshooting actions

**Success Alerts Include**:
- Pipeline completion summary
- Layer-by-layer status
- Data availability confirmation

## Environment Variables

Required environment variables (configured in `.env` file):

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

## Task Dependencies

```
start
  ↓
validate_source_files
  ↓
ingest_bronze_layer
  ↓
validate_bronze_layer
  ↓
silver_transformations (parallel)
  ↓
validate_silver_layer
  ↓
dbt_gold_layer (sequential)
  ├─ dbt_run_staging
  ├─ dbt_test_staging
  ├─ dbt_run_dimensions
  ├─ dbt_run_facts
  └─ dbt_test_gold
  ↓
validate_gold_layer
  ↓
generate_data_quality_report
  ↓
refresh_superset_cache
  ↓
end
```

## Running the DAG

### Manual Trigger

From Airflow UI:
1. Navigate to DAGs page
2. Find `healthcare_etl_pipeline`
3. Click the "Play" button to trigger manually

From CLI:
```bash
airflow dags trigger healthcare_etl_pipeline
```

### Scheduled Runs

The DAG runs automatically daily at 2:00 AM UTC. No manual intervention required.

### Backfill (if needed)

```bash
airflow dags backfill healthcare_etl_pipeline \
  --start-date 2025-01-01 \
  --end-date 2025-01-31
```

## Monitoring

### Airflow UI

- **DAG View**: Overall pipeline status and task dependencies
- **Graph View**: Visual representation of task flow
- **Gantt Chart**: Task execution timeline
- **Task Logs**: Detailed logs for each task

### Data Quality Reports

Generated reports are stored in:
```
/opt/airflow/logs/data_quality_report.json
```

### Alerts

Alert files are stored in:
```
/opt/airflow/logs/alerts/alert_YYYYMMDD_HHMMSS.json
```

## Troubleshooting

### Common Issues

**1. Missing CSV Files**
- **Error**: `BronzeIngestionError: Missing required CSV file(s)`
- **Solution**: Ensure all 9 CSV files are in `SOURCE_CSV_PATH`

**2. Data Quality Validation Failure**
- **Error**: `Silver layer validation failed`
- **Solution**: Check Great Expectations reports in `great_expectations/uncommitted/data_docs/`

**3. dbt Test Failures**
- **Error**: `dbt test failed`
- **Solution**: Review dbt logs and fix data issues or model logic

**4. Database Connection Error**
- **Error**: `Failed to connect to PostgreSQL`
- **Solution**: Verify database is running and credentials are correct

**5. Task Timeout**
- **Error**: `Task exceeded execution_timeout`
- **Solution**: Increase timeout for specific task or investigate performance issues

### Debug Mode

To run tasks in debug mode:

```python
# In Airflow UI, click on task → "Run" → "Run with config"
# Or use CLI:
airflow tasks test healthcare_etl_pipeline <task_id> 2025-01-15
```

## Performance Metrics

Expected execution times (for ~126K rows):
- Bronze ingestion: < 2 minutes
- Silver transformation: < 10 minutes (parallel)
- dbt Gold layer: < 15 minutes
- Total pipeline: < 30 minutes

## Maintenance

### Regular Tasks

1. **Monitor disk space**: Bronze/Silver layers accumulate data
2. **Review data quality reports**: Check for trends in validation failures
3. **Update expectation suites**: As data patterns change
4. **Optimize dbt models**: If execution time increases

### Cleanup

Old data can be archived/deleted:
```bash
# Remove Bronze/Silver data older than 30 days
find /opt/airflow/data/bronze -type d -mtime +30 -exec rm -rf {} \;
find /opt/airflow/data/silver -type d -mtime +30 -exec rm -rf {} \;
```

## Support

For issues or questions:
- Check Airflow logs: `/opt/airflow/logs/`
- Review data quality reports: `/opt/airflow/logs/data_quality_report.json`
- Contact: data-team@hospital.com
