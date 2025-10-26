# Great Expectations Data Quality Validation

This directory contains the Great Expectations configuration for validating data quality in the Healthcare ETL Pipeline.

## Structure

```
great_expectations/
├── great_expectations.yml          # Main configuration file
├── expectations/                   # Expectation suites (validation rules)
│   ├── bronze_*.json              # Bronze layer validation suites
│   └── silver_*.json              # Silver layer validation suites
├── checkpoints/                    # Checkpoint configurations
│   ├── bronze_validation_checkpoint.yml
│   └── silver_validation_checkpoint.yml
└── uncommitted/                    # Runtime data (not in version control)
    ├── validations/               # Validation results
    └── data_docs/                 # Generated documentation
```

## Validation Suites

### Bronze Layer Validation
- **Purpose**: Validate raw CSV files for basic integrity
- **Checks**:
  - Row count validation (at least 1 row)
  - Primary key uniqueness and non-null checks
  - Required column existence
  - File format validation

### Silver Layer Validation
- **Purpose**: Validate cleaned and transformed Parquet files
- **Checks**:
  - Schema validation (column names and types)
  - Value range checks (age 0-120, costs >= 0)
  - ID pattern matching (PAT*, ENC*, PRO* formats)
  - Data type validation
  - Audit column presence

## Usage

### Using the Data Quality Module

```python
from data_quality import DataQualityValidator

# Initialize validator
validator = DataQualityValidator()

# Validate Bronze layer
bronze_result = validator.validate_bronze_layer(run_date="2025-10-24")

# Validate Silver layer
silver_result = validator.validate_silver_layer(run_date="2025-10-24")

# Generate comprehensive report
validator.generate_data_quality_report([bronze_result, silver_result])
```

### Using the Command Line

```bash
# Validate both layers
python3 data_quality.py --layer both --date 2025-10-24

# Validate only Silver layer
python3 data_quality.py --layer silver --date 2025-10-24

# Validate only Bronze layer
python3 data_quality.py --layer bronze --date 2025-10-24
```

## Checkpoints

Checkpoints define which expectation suites to run and what actions to take with the results.

### Bronze Validation Checkpoint
- Validates all 9 Bronze layer CSV files
- Stores validation results
- Updates data docs

### Silver Validation Checkpoint
- Validates all 9 Silver layer Parquet files
- Stores validation results
- Updates data docs

## Validation Results

Results are stored in:
- `uncommitted/validations/` - Individual validation results
- `logs/data_quality_report.json` - Comprehensive report
- `logs/alerts/` - Alert files for validation failures

## Alerts

When validation failures occur:
1. Detailed error logs are written to the console
2. Alert files are created in `logs/alerts/`
3. Critical alerts are logged for monitoring systems

## Adding New Expectations

To add new validation rules:

1. Create or modify expectation suite JSON files in `expectations/`
2. Add expectations following Great Expectations syntax
3. Update checkpoints if needed
4. Test with sample data

Example expectation:
```json
{
  "expectation_type": "expect_column_values_to_be_between",
  "kwargs": {
    "column": "age",
    "min_value": 0,
    "max_value": 120
  }
}
```

## Integration with Airflow

The data quality validation is designed to be integrated into Airflow DAGs:

```python
from airflow.operators.python import PythonOperator
from data_quality import DataQualityValidator

def validate_silver_layer(**context):
    validator = DataQualityValidator()
    result = validator.validate_silver_layer(context['ds'])
    if not result['success']:
        raise ValueError("Data quality validation failed")

validate_task = PythonOperator(
    task_id='validate_silver_layer',
    python_callable=validate_silver_layer,
    dag=dag
)
```

## Troubleshooting

### Common Issues

1. **Empty batch_list error**: Check that data files exist in the configured directories
2. **Regex pattern mismatch**: Verify file naming conventions match the regex patterns
3. **Column not found**: Ensure expectation suite column names match actual data

### Debugging

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

View validation details:
```bash
cat logs/data_quality_report.json | python3 -m json.tool
```
