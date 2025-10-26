# Healthcare ETL Pipeline - Integration Test

## Overview

This integration test validates the complete end-to-end functionality of the Healthcare ETL Pipeline, including Bronze layer ingestion, Silver layer transformation, Gold layer (dbt) structure, and data quality validation.

## Test Components

### 1. Test Data Generation (`create_test_data.py`)

Creates sample CSV files with 100 rows each for all 9 tables, including edge cases:

- **Missing values**: Phone numbers, emails, address fields
- **Duplicate records**: One duplicate per table to test deduplication
- **Invalid date logic**: Admission date after discharge date
- **Negative amounts**: Invalid billing amounts
- **Zero amounts**: Edge case for payment processing
- **Missing optional fields**: Various optional fields left empty

**Usage:**
```bash
python create_test_data.py
```

**Output:** Creates test datasets in `./test_data/` directory

### 2. Integration Test Script (`integration_test.py`)

Runs the complete pipeline with test data and validates all layers.

**Usage:**
```bash
python integration_test.py
```

## Test Validation

### Test 1: Bronze Layer Ingestion

Validates:
- ✅ All 9 CSV files are copied to Bronze layer with timestamp prefix
- ✅ Bronze directory structure is created (`data/bronze/YYYY-MM-DD/`)
- ✅ Metadata file (`_metadata.json`) is generated
- ✅ Row counts match source files
- ✅ Checksums are calculated for all files
- ✅ File sizes are recorded

**Expected Output:**
```
Bronze Layer:
  - 9 CSV files in test_output/bronze/2025-10-24/
  - _metadata.json with file details
  - Total: 909 rows across all tables
```

### Test 2: Silver Layer Transformation

Validates:
- ✅ Parquet files are created for all 9 tables
- ✅ Silver directory structure is created (`data/silver/YYYY-MM-DD/`)
- ✅ Row counts are reasonable (accounting for deduplication)
- ✅ Audit columns are present: `load_timestamp`, `source_file`, `record_hash`
- ✅ Audit columns have no null values
- ✅ Date standardization is applied
- ✅ Data type conversions are applied
- ✅ Duplicates are removed

**Expected Output:**
```
Silver Layer:
  - 9 Parquet files in test_output/silver/2025-10-24/
  - Row counts: 675 total (after deduplication)
  - Compression: Snappy
  - All audit columns present and populated
```

### Test 3: Gold Layer (dbt)

Validates:
- ✅ dbt project structure exists
- ✅ Staging models are present (9 models)
- ✅ Dimension models are present (5 models)
- ✅ Fact models are present (4 models)

**Note:** Full dbt execution requires database connection and is not run in this test.

### Test 4: Data Quality Validation

Validates:
- ✅ Great Expectations configuration exists
- ✅ Bronze expectation suites are defined (9 suites)
- ✅ Silver expectation suites are defined (9 suites)
- ✅ Checkpoints are configured (2 checkpoints)

**Note:** Full Great Expectations validation requires running checkpoints and is not executed in this test.

## Test Results

### Success Criteria

All tests must pass for the integration test to succeed:

```
✅ Bronze Layer:     PASSED
✅ Silver Layer:     PASSED
✅ Gold Layer:       PASSED
✅ Data Quality:     PASSED
```

### Exit Codes

- **0**: All tests passed
- **1**: One or more tests failed

## Test Output

### Directory Structure

```
test_output/
├── bronze/
│   └── 2025-10-24/
│       ├── 2025-10-24_patients.csv
│       ├── 2025-10-24_encounters.csv
│       ├── ... (7 more CSV files)
│       └── _metadata.json
└── silver/
    └── 2025-10-24/
        ├── patients.parquet
        ├── encounters.parquet
        └── ... (7 more Parquet files)
```

### Metadata File Example

```json
{
  "run_date": "2025-10-24",
  "ingestion_timestamp": "2025-10-24T21:43:05.620249+00:00",
  "total_files": 9,
  "total_rows": 909,
  "total_size_bytes": 97754,
  "files": [
    {
      "source_file": "patients.csv",
      "bronze_file": "2025-10-24_patients.csv",
      "row_count": 101,
      "file_size_bytes": 15811,
      "checksum_md5": "21198292c635c3ac4e88eb06c5a10b49",
      "ingestion_timestamp": "2025-10-24T21:43:05.614391+00:00",
      "run_date": "2025-10-24"
    }
    // ... more files
  ]
}
```

## Edge Cases Tested

### 1. Missing Data Handling

- **Phone numbers**: Rows 5-10 have empty phone numbers
- **Emails**: Rows 15-20 have empty emails
- **Address fields**: Rows 25-28 have empty address, city, state, zip

**Expected Behavior:** Missing data strategies from config are applied (e.g., fill with 'NOT_PROVIDED')

### 2. Duplicate Records

- Each table has 1 duplicate record added
- **Expected Behavior:** Duplicates are removed during Silver transformation

### 3. Invalid Date Logic

- Encounter with admission_date > discharge_date
- **Expected Behavior:** Record is processed but would fail data quality checks

### 4. Invalid Amounts

- Negative billing amount in row 5
- Zero payment amount in row 8
- **Expected Behavior:** Records are processed but would fail data quality validation

## Performance Benchmarks

Based on test execution with 100 rows per table:

- **Bronze Ingestion**: < 1 second
- **Silver Transformation**: < 1 second
- **Total Execution Time**: < 1 second

**Note:** These are test benchmarks. Production performance with 126K+ rows will be significantly longer.

## Troubleshooting

### Test Fails at Bronze Layer

**Issue:** Missing CSV files
**Solution:** Run `python create_test_data.py` first to generate test data

**Issue:** Permission denied
**Solution:** Check write permissions for `test_output/` directory

### Test Fails at Silver Layer

**Issue:** Configuration file not found
**Solution:** Ensure `config/silver_table_config.yaml` exists

**Issue:** Parquet write error
**Solution:** Check that `pyarrow` is installed: `pip install pyarrow`

### Test Fails at Gold Layer

**Issue:** dbt project not found
**Solution:** Ensure `dbt_project/` directory exists with models

### Test Fails at Data Quality

**Issue:** Great Expectations not configured
**Solution:** Ensure `great_expectations/` directory exists with expectation suites

## Cleanup

To remove test output after running tests:

```bash
rm -rf test_output/
```

Or uncomment the cleanup line in `integration_test.py`:

```python
# In the finally block
cleanup_test_environment()
```

## CI/CD Integration

To integrate this test into a CI/CD pipeline:

```yaml
# Example GitHub Actions workflow
- name: Run Integration Tests
  run: |
    python create_test_data.py
    python integration_test.py
```

## Requirements

- Python 3.8+
- pandas
- pyarrow
- pyyaml
- All pipeline dependencies (see `requirements.txt`)

## Related Files

- `create_test_data.py`: Test data generation script
- `integration_test.py`: Main integration test script
- `bronze_ingestion.py`: Bronze layer ingestion module
- `silver_transformation.py`: Silver layer transformation module
- `config/silver_table_config.yaml`: Silver layer configuration
- `test_data/`: Test CSV files (generated)
- `test_output/`: Test output directory (generated)

## Future Enhancements

1. **Full dbt Execution**: Add database setup and run dbt models
2. **Great Expectations Validation**: Execute checkpoints and validate results
3. **Performance Testing**: Add benchmarks for larger datasets
4. **Airflow DAG Testing**: Test complete DAG execution
5. **Gold Layer Validation**: Query PostgreSQL and validate star schema
6. **Data Quality Metrics**: Generate detailed quality reports
