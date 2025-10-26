# Logging and Error Handling Documentation

This document describes the centralized logging and alerting system implemented for the Healthcare ETL Pipeline.

## Overview

The pipeline now includes:
- **Centralized JSON logging** with structured metadata
- **Comprehensive error handling** with retry logic
- **Email alerting system** for critical failures
- **Log rotation and retention** policies

## Logging Module (`logger.py`)

### Features

- **Structured JSON logging** for easy parsing and analysis
- **Multiple log levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Automatic log rotation** (10 MB per file, 10 backup files)
- **Console and file output** with different formats
- **Metadata support** for contextual information
- **Airflow integration** with DAG/task context

### Usage

#### Basic Usage

```python
from logger import get_logger

# Create logger
logger = get_logger(__name__)

# Log messages with metadata
logger.info("Processing started", metadata={'rows': 1000, 'file': 'patients.csv'})
logger.error("Processing failed", metadata={'error': str(e), 'file': 'patients.csv'})
```

#### With Airflow Context

```python
from logger import setup_airflow_logging

# Setup logger with Airflow context
logger = setup_airflow_logging(
    dag_id="healthcare_etl_pipeline",
    task_id="bronze_ingest_patients",
    run_id="scheduled__2025-01-15T02:00:00+00:00"
)

logger.info("Task started")
```

### Configuration

Set environment variables to configure logging:

```bash
# Log directory (default: logs)
export LOG_DIR="logs"

# Log level (default: INFO)
export LOG_LEVEL="INFO"

# Log file name (default: pipeline.log)
export LOG_FILE="pipeline.log"
```

### Log Format

**Console Output** (human-readable):
```
2025-10-24 02:00:00,123 - bronze_ingestion - INFO - Processing started
```

**File Output** (JSON):
```json
{
  "timestamp": "2025-10-24T02:00:00.123456+00:00",
  "level": "INFO",
  "name": "bronze_ingestion",
  "message": "Processing started",
  "metadata": {
    "rows": 1000,
    "file": "patients.csv"
  },
  "logger": "bronze_ingestion",
  "module": "bronze_ingestion",
  "function": "ingest_csv_files",
  "line": 123,
  "process_id": 12345,
  "thread_id": 67890
}
```

### Log Rotation

- **Max file size**: 10 MB
- **Backup count**: 10 files
- **Retention**: 30 days (configurable)

To clean up old logs:

```python
from logger import cleanup_old_logs

cleanup_old_logs(log_dir='logs', retention_days=30)
```

## Alerting Module (`alerts.py`)

### Features

- **Email notifications** via SMTP
- **Multiple severity levels**: CRITICAL, WARNING, INFO
- **Alert templates** for common scenarios
- **Alert logging** to JSON files
- **Configurable recipients** per alert type

### Usage

#### Basic Alert

```python
from alerts import get_alert_manager

# Get alert manager
alert_manager = get_alert_manager()

# Send custom alert
alert_manager.send_alert(
    alert_type="CUSTOM_ERROR",
    severity="CRITICAL",
    subject="Custom Error Occurred",
    message="Detailed error message here",
    metadata={'key': 'value'}
)
```

#### Pipeline Failure Alert

```python
alert_manager.send_pipeline_failure_alert(
    pipeline_name="healthcare_etl_pipeline",
    task_name="bronze_ingest_patients",
    error_message="File not found: patients.csv",
    metadata={'source_dir': '/data/source'}
)
```

#### Data Quality Alert

```python
alert_manager.send_data_quality_alert(
    layer="Silver",
    validation_name="silver_validation_checkpoint",
    failure_details={
        'success_rate': 85.5,
        'failed_count': 3,
        'total_validations': 20
    }
)
```

#### Database Connection Alert

```python
alert_manager.send_database_connection_alert(
    database="healthcare_warehouse",
    error_message="Connection timeout",
    retry_count=3
)
```

#### Performance Alert

```python
alert_manager.send_performance_alert(
    task_name="silver_transform_encounters",
    execution_time=125.5,
    threshold=60.0
)
```

### Configuration

Set environment variables to configure alerting:

```bash
# SMTP Configuration
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USER="your-email@gmail.com"
export SMTP_PASSWORD="your-app-password"

# Alert Configuration
export ALERT_FROM_EMAIL="etl-alerts@hospital.com"
export ALERT_RECIPIENTS="data-team@hospital.com,ops-team@hospital.com"
export ENABLE_EMAIL_ALERTS="true"
export ALERT_LOG_DIR="logs/alerts"
```

### Alert Templates

Alerts are automatically formatted with:
- **Plain text** version for email clients without HTML support
- **HTML** version with color-coded severity levels
- **Metadata** section with additional context

### Alert Logging

All alerts are logged to JSON files in `logs/alerts/` directory:

```json
{
  "alert_type": "PIPELINE_FAILURE",
  "severity": "CRITICAL",
  "subject": "Pipeline Failure: healthcare_etl_pipeline - bronze_ingest_patients",
  "message": "The ETL pipeline has failed...",
  "metadata": {
    "source_dir": "/data/source",
    "expected_files": 9
  },
  "timestamp": "2025-10-24T02:00:00.123456+00:00",
  "recipients": ["data-team@hospital.com"]
}
```

## Error Handling

### Bronze Ingestion

Enhanced error handling includes:
- File validation with detailed error messages
- Checksum calculation with retry logic
- Graceful handling of missing files
- Cleanup on partial failures

### Silver Transformation

Enhanced error handling includes:
- Data sample logging on errors
- Type conversion error handling
- Deduplication error recovery
- Detailed transformation metrics

### Data Quality Validation

Enhanced error handling includes:
- Checkpoint execution retry logic
- Validation result parsing with error details
- Automatic alert generation on failures
- Comprehensive failure logging

### Database Operations

Enhanced error handling includes:
- **Retry logic** with exponential backoff
- **Connection pooling** error handling
- **Transaction rollback** on failures
- **Detailed error logging** with stack traces

Example retry configuration:

```python
def load_with_retry(data, max_retries=3, retry_delay=5):
    for attempt in range(1, max_retries + 1):
        try:
            # Attempt operation
            return load_data(data)
        except OperationalError as e:
            if attempt < max_retries:
                logger.warning(f"Retry {attempt}/{max_retries} after {retry_delay}s")
                time.sleep(retry_delay)
            else:
                logger.error(f"Failed after {max_retries} attempts")
                raise
```

## Best Practices

### Logging

1. **Use appropriate log levels**:
   - DEBUG: Detailed diagnostic information
   - INFO: General informational messages
   - WARNING: Warning messages for recoverable issues
   - ERROR: Error messages for failures
   - CRITICAL: Critical failures requiring immediate attention

2. **Include metadata**:
   ```python
   logger.info("Processing file", metadata={
       'file': filename,
       'rows': row_count,
       'execution_time': elapsed_time
   })
   ```

3. **Log at key points**:
   - Start and end of operations
   - Before and after external calls
   - On error conditions
   - On performance milestones

### Error Handling

1. **Catch specific exceptions**:
   ```python
   try:
       process_data()
   except FileNotFoundError as e:
       logger.error("File not found", metadata={'error': str(e)})
       raise
   except ValueError as e:
       logger.error("Invalid data", metadata={'error': str(e)})
       raise
   ```

2. **Provide context in errors**:
   ```python
   try:
       df = pd.read_csv(file_path)
   except Exception as e:
       error_msg = f"Failed to read {file_path}: {str(e)}"
       logger.error(error_msg, metadata={'file': file_path, 'error': str(e)})
       raise CustomError(error_msg) from e
   ```

3. **Clean up on failures**:
   ```python
   try:
       temp_file = create_temp_file()
       process_file(temp_file)
   except Exception as e:
       if temp_file.exists():
           temp_file.unlink()
       raise
   ```

### Alerting

1. **Use appropriate severity**:
   - CRITICAL: Requires immediate action (pipeline failures, data corruption)
   - WARNING: Requires attention but not urgent (performance degradation)
   - INFO: Informational only (successful completion)

2. **Include actionable information**:
   ```python
   alert_manager.send_alert(
       alert_type="DATA_QUALITY_FAILURE",
       severity="CRITICAL",
       subject="Data Quality Failure in Silver Layer",
       message="Validation failed with 15% error rate",
       metadata={
           'layer': 'Silver',
           'validation': 'silver_patients_suite',
           'error_rate': 15.0,
           'action': 'Review data quality report at logs/data_quality_report.json'
       }
   )
   ```

3. **Avoid alert fatigue**:
   - Don't send alerts for expected conditions
   - Batch similar alerts when possible
   - Use WARNING for non-critical issues

## Monitoring

### Log Analysis

Query JSON logs using tools like `jq`:

```bash
# Find all errors in the last hour
cat logs/pipeline.log | jq 'select(.level == "ERROR")'

# Count errors by module
cat logs/pipeline.log | jq -r 'select(.level == "ERROR") | .module' | sort | uniq -c

# Find slow operations
cat logs/pipeline.log | jq 'select(.metadata.execution_time_seconds > 60)'
```

### Alert Review

Review alert history:

```bash
# List all alerts
ls -lh logs/alerts/

# View recent critical alerts
cat logs/alerts/alert_*.json | jq 'select(.severity == "CRITICAL")'

# Count alerts by type
cat logs/alerts/alert_*.json | jq -r '.alert_type' | sort | uniq -c
```

## Troubleshooting

### Logs Not Being Created

1. Check log directory permissions
2. Verify LOG_DIR environment variable
3. Check disk space

### Emails Not Being Sent

1. Verify SMTP configuration
2. Check ENABLE_EMAIL_ALERTS is set to "true"
3. Test SMTP connection manually
4. Check firewall rules for SMTP port

### Performance Issues

1. Reduce log level to WARNING or ERROR
2. Increase log rotation size
3. Use asynchronous logging for high-volume scenarios

## Integration with Airflow

The logging and alerting modules integrate seamlessly with Airflow:

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from logger import setup_airflow_logging
from alerts import get_alert_manager

def my_task(**context):
    # Setup logging with Airflow context
    logger = setup_airflow_logging(
        dag_id=context['dag'].dag_id,
        task_id=context['task'].task_id,
        run_id=context['run_id']
    )
    
    alert_manager = get_alert_manager()
    
    try:
        logger.info("Task started")
        # Your task logic here
        logger.info("Task completed")
    except Exception as e:
        logger.error(f"Task failed: {str(e)}")
        alert_manager.send_pipeline_failure_alert(
            pipeline_name=context['dag'].dag_id,
            task_name=context['task'].task_id,
            error_message=str(e)
        )
        raise

dag = DAG('my_dag', ...)
task = PythonOperator(task_id='my_task', python_callable=my_task, dag=dag)
```

## Summary

The centralized logging and alerting system provides:
- ✅ Structured JSON logging for easy analysis
- ✅ Comprehensive error handling with retry logic
- ✅ Email alerts for critical failures
- ✅ Log rotation and retention
- ✅ Airflow integration
- ✅ Performance monitoring
- ✅ Detailed error context and stack traces

For questions or issues, contact the data engineering team.
