# dbt Tests Documentation

This directory contains custom data quality tests for the healthcare ETL pipeline.

## Test Categories

### 1. Generic Tests (in schema.yml files)

These are built-in dbt tests applied to individual columns:

- **unique**: Ensures column values are unique
- **not_null**: Ensures column has no null values
- **relationships**: Validates foreign key relationships
- **accepted_values**: Ensures column values are from a predefined list
- **dbt_utils.accepted_range**: Validates numeric values are within a range

### 2. Custom Tests (in this directory)

#### assert_referential_integrity.sql
Tests that all foreign key relationships are valid across fact and dimension tables.

**Checks:**
- fact_encounter → dim_patient
- fact_encounter → dim_provider
- fact_encounter → dim_diagnosis
- fact_billing → fact_encounter
- fact_billing → dim_patient
- fact_lab_test → fact_encounter
- fact_denial → fact_billing

**Failure Condition:** Any orphaned foreign keys found

#### assert_no_orphaned_records.sql
Tests that required foreign keys are not null in fact tables.

**Checks:**
- Encounters must have patients
- Billing records must have encounters
- Lab tests must have encounters
- Denials must have billing records

**Failure Condition:** Any null required foreign keys found

#### assert_date_logic.sql
Tests that date sequences are logically valid.

**Checks:**
- Encounter admission_date <= discharge_date
- Patient SCD valid_from <= valid_to

**Failure Condition:** Any invalid date sequences found

#### assert_financial_metrics.sql
Tests that financial calculations are correct and consistent.

**Checks:**
- paid_amount + denied_amount <= billed_amount
- payment_rate calculation is correct
- Denied amounts match between billing and denial tables

**Failure Condition:** Any financial inconsistencies found

## Running Tests

### Run all tests
```bash
dbt test
```

### Run tests for specific models
```bash
dbt test --select fact_encounter
dbt test --select dim_patient
```

### Run only custom tests
```bash
dbt test --select test_type:singular
```

### Run only generic tests
```bash
dbt test --select test_type:generic
```

## Test Results

Test results are stored in the `test_results` schema (configured in dbt_project.yml).

Failed test results can be queried:
```sql
SELECT * FROM test_results.assert_referential_integrity;
```

## Adding New Tests

### Generic Tests
Add to the `schema.yml` file in the appropriate model directory:

```yaml
columns:
  - name: column_name
    tests:
      - unique
      - not_null
```

### Custom Tests
Create a new `.sql` file in this directory. The test should return rows only when it fails:

```sql
-- Test description
select
    column_name,
    count(*) as issue_count
from {{ ref('model_name') }}
where <condition_that_should_not_be_true>
group by column_name
```
