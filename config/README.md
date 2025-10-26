# Configuration Management System

This directory contains the configuration management system for the Healthcare ETL Pipeline.

## Files

- **pipeline_config.yaml**: Main pipeline configuration file with all settings for Bronze/Silver/Gold layers
- **silver_table_config.yaml**: Table-specific transformation rules for Silver layer processing

## Configuration Loader

The `config_loader.py` module provides a centralized configuration management system with:

- Environment variable substitution using `${VAR_NAME}` syntax
- Configuration validation at startup
- Default value provision
- Environment-specific overrides (development, staging, production)
- Singleton pattern for global configuration access

## Usage

### Basic Usage

```python
from config_loader import get_config

# Get configuration instance
config = get_config()

# Get specific values
bronze_path = config.get('bronze.source_path')
silver_path = config.get('silver.target_path')
db_host = config.get('gold.database.host')

# Get entire sections
bronze_config = config.get_bronze_config()
silver_config = config.get_silver_config()
gold_config = config.get_gold_config()
```

### Helper Methods

```python
# Get database connection string
conn_string = config.get_database_connection_string()
# Returns: postgresql://user:password@host:port/database

# Get run date (defaults to today)
run_date = config.get_run_date()

# Check feature flags
if config.is_feature_enabled('enable_bronze_validation'):
    # Run validation

# Get task timeouts
timeout = config.get_task_timeout('bronze_ingestion')

# Get performance benchmarks
max_time = config.get_benchmark('bronze_ingestion_max')

# Get data quality settings
should_fail = config.should_fail_on_data_quality_error()
threshold = config.get_data_quality_warning_threshold()

# Get table list
tables = config.get_table_list()
```

## Environment Variables

Configuration values can reference environment variables using `${VAR_NAME}` syntax.

Required environment variables (set in `.env` file):

```bash
# Pipeline
PIPELINE_NAME=healthcare_etl
PIPELINE_VERSION=1.0.0

# Paths
SOURCE_CSV_PATH=/opt/airflow/dataset
BRONZE_DATA_PATH=/opt/airflow/data/bronze
SILVER_DATA_PATH=/opt/airflow/data/silver

# Database
POSTGRES_HOST=warehouse-db
POSTGRES_PORT=5432
POSTGRES_DB=healthcare_warehouse
POSTGRES_USER=etl_user
POSTGRES_PASSWORD=etl_password

# Data Quality
DATA_QUALITY_FAIL_ON_ERROR=true
DATA_QUALITY_WARNING_THRESHOLD=0.05

# Alerting
ALERT_EMAIL=data-team@hospital.com
SMTP_PASSWORD=
SLACK_WEBHOOK_URL=

# Environment
ENVIRONMENT=development  # Options: development, staging, production
```

## Environment-Specific Overrides

The configuration system supports environment-specific overrides. Set the `ENVIRONMENT` variable to one of:

- **development**: Debug logging, manual DAG triggers, data quality warnings only
- **staging**: Info logging, scheduled runs at 4 AM UTC
- **production**: Warning logging, scheduled runs at 2 AM UTC, strict data quality, all alerts enabled

Example override in `pipeline_config.yaml`:

```yaml
environments:
  development:
    logging:
      level: DEBUG
    data_quality:
      failure_handling:
        fail_on_error: false
  
  production:
    logging:
      level: WARNING
    data_quality:
      failure_handling:
        fail_on_error: true
```

## Configuration Validation

The configuration loader validates required parameters at startup:

- Required sections: pipeline, bronze, silver, gold, data_quality
- Pipeline name must be set
- Bronze tables list must not be empty
- Database connection parameters must be complete
- Data quality thresholds must be valid numbers between 0 and 1

## Command-Line Interface

Test and inspect configuration:

```bash
# Validate configuration
python config_loader.py

# Dump full configuration as JSON
python config_loader.py --dump

# Use custom config file
python config_loader.py path/to/config.yaml
```

## Configuration Structure

### Pipeline Section
- Basic pipeline metadata (name, version, description)

### Bronze Layer
- Source and target paths
- Expected table list
- File validation settings
- Metadata generation options

### Silver Layer
- Source and target paths
- Table configuration file reference
- Date format settings
- Parquet compression settings
- Audit column configuration
- Deduplication settings

### Gold Layer
- Database connection parameters
- Connection pool settings
- dbt configuration
- Incremental loading strategy

### Data Quality
- Great Expectations settings
- Validation checkpoints
- Failure handling rules
- Validation rules (row counts, schema, primary keys, referential integrity, value ranges, date logic, patterns)

### Airflow
- DAG configuration (schedule, start date, tags)
- Default task arguments
- Task timeout settings
- Email and Slack alerting

### Logging
- Log level and format
- File and console logging
- Structured logging fields
- Log retention policies

### Alerting
- Email and Slack channel configuration
- Alert severity levels
- Alert templates

### Performance
- Performance benchmarks
- Monitoring settings
- Optimization flags

### Feature Flags
- Enable/disable specific features
- Useful for gradual rollout and testing

## Best Practices

1. **Never commit secrets**: Use environment variables for sensitive data (passwords, API keys)
2. **Use environment overrides**: Configure different settings for dev/staging/prod
3. **Validate early**: Configuration is validated at startup to catch errors early
4. **Use feature flags**: Enable/disable features without code changes
5. **Document changes**: Update this README when adding new configuration options
6. **Test configuration**: Run `python config_loader.py` after making changes

## Troubleshooting

### Environment variables not substituted
- Ensure `.env` file exists and contains required variables
- Check that `python-dotenv` is installed
- Verify environment variable names match exactly (case-sensitive)

### Configuration validation fails
- Check that all required sections exist
- Verify data types (numbers, booleans, strings)
- Ensure database parameters are complete
- Check that thresholds are between 0 and 1

### Missing configuration keys
- Use `config.get('key.path', default_value)` to provide defaults
- Check for typos in key paths (dot-separated)
- Verify the key exists in `pipeline_config.yaml`

## Integration with Existing Modules

The configuration system integrates seamlessly with existing pipeline modules:

```python
from config_loader import get_config
from bronze_ingestion import ingest_csv_files
from silver_transformation import transform_bronze_to_silver

config = get_config()

# Use configuration in bronze ingestion
bronze_config = config.get_bronze_config()
ingest_csv_files(
    source_dir=bronze_config['source_path'],
    bronze_dir=bronze_config['target_path'],
    run_date=config.get_run_date()
)

# Use configuration in silver transformation
silver_config = config.get_silver_config()
transform_bronze_to_silver(
    bronze_dir=bronze_config['target_path'],
    silver_dir=silver_config['target_path'],
    config_file=silver_config['table_config_file'],
    run_date=config.get_run_date()
)
```
