# Healthcare ETL Pipeline - DAG Structure

## Visual Representation

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         HEALTHCARE ETL PIPELINE                          │
│                        Daily at 2:00 AM UTC                              │
└─────────────────────────────────────────────────────────────────────────┘

                              ┌───────┐
                              │ START │
                              └───┬───┘
                                  │
                    ┌─────────────▼──────────────┐
                    │ validate_source_files      │
                    │ (5 min timeout)            │
                    │ • Check 9 CSV files exist  │
                    └─────────────┬──────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │ ingest_bronze_layer        │
                    │ (10 min timeout)           │
                    │ • Copy CSV to Bronze       │
                    │ • Generate metadata        │
                    └─────────────┬──────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │ validate_bronze_layer      │
                    │ (5 min timeout)            │
                    │ • Validate row counts      │
                    └─────────────┬──────────────┘
                                  │
        ┌─────────────────────────▼─────────────────────────┐
        │         SILVER TRANSFORMATIONS (Parallel)          │
        │                (15 min timeout each)               │
        ├────────────────────────────────────────────────────┤
        │  ┌──────────────────┐  ┌──────────────────┐       │
        │  │ transform_       │  │ transform_       │       │
        │  │ patients         │  │ encounters       │       │
        │  └──────────────────┘  └──────────────────┘       │
        │                                                    │
        │  ┌──────────────────┐  ┌──────────────────┐       │
        │  │ transform_       │  │ transform_       │       │
        │  │ diagnoses        │  │ procedures       │       │
        │  └──────────────────┘  └──────────────────┘       │
        │                                                    │
        │  ┌──────────────────┐  ┌──────────────────┐       │
        │  │ transform_       │  │ transform_       │       │
        │  │ medications      │  │ lab_tests        │       │
        │  └──────────────────┘  └──────────────────┘       │
        │                                                    │
        │  ┌──────────────────┐  ┌──────────────────┐       │
        │  │ transform_       │  │ transform_       │       │
        │  │ claims_and_      │  │ providers        │       │
        │  │ billing          │  │                  │       │
        │  └──────────────────┘  └──────────────────┘       │
        │                                                    │
        │  ┌──────────────────┐                             │
        │  │ transform_       │                             │
        │  │ denials          │                             │
        │  └──────────────────┘                             │
        └────────────────────────┬───────────────────────────┘
                                 │
                   ┌─────────────▼──────────────┐
                   │ validate_silver_layer      │
                   │ (20 min timeout)           │
                   │ • Great Expectations       │
                   │ • Data quality checks      │
                   └─────────────┬──────────────┘
                                 │
        ┌────────────────────────▼────────────────────────┐
        │         DBT GOLD LAYER (Sequential)             │
        ├─────────────────────────────────────────────────┤
        │                                                 │
        │  ┌──────────────────────────────────────────┐   │
        │  │ dbt_run_staging (15 min)                 │   │
        │  │ • Read Silver Parquet                    │   │
        │  │ • Create staging models                  │   │
        │  └──────────────────┬───────────────────────┘   │
        │                     │                           │
        │  ┌──────────────────▼───────────────────────┐   │
        │  │ dbt_test_staging (10 min)                │   │
        │  │ • Test staging models                    │   │
        │  └──────────────────┬───────────────────────┘   │
        │                     │                           │
        │  ┌──────────────────▼───────────────────────┐   │
        │  │ dbt_run_dimensions (15 min)              │   │
        │  │ • Create dimension tables                │   │
        │  │ • SCD Type 2 for dim_patient             │   │
        │  └──────────────────┬───────────────────────┘   │
        │                     │                           │
        │  ┌──────────────────▼───────────────────────┐   │
        │  │ dbt_run_facts (20 min)                   │   │
        │  │ • Create fact tables                     │   │
        │  │ • Join dimensions                        │   │
        │  └──────────────────┬───────────────────────┘   │
        │                     │                           │
        │  ┌──────────────────▼───────────────────────┐   │
        │  │ dbt_test_gold (15 min)                   │   │
        │  │ • Test all Gold models                   │   │
        │  │ • Referential integrity                  │   │
        │  └──────────────────┬───────────────────────┘   │
        │                     │                           │
        └─────────────────────┼───────────────────────────┘
                              │
                ┌─────────────▼──────────────┐
                │ validate_gold_layer        │
                │ (10 min timeout)           │
                │ • Check table row counts   │
                └─────────────┬──────────────┘
                              │
                ┌─────────────▼──────────────┐
                │ generate_data_quality_     │
                │ report (5 min timeout)     │
                │ • Compile all validations  │
                └─────────────┬──────────────┘
                              │
                ┌─────────────▼──────────────┐
                │ refresh_superset_cache     │
                │ (5 min timeout)            │
                │ • Update dashboards        │
                └─────────────┬──────────────┘
                              │
                              ▼
                          ┌───────┐
                          │  END  │
                          └───────┘
```

## Task Groups

### 1. Bronze Layer Tasks
- **Purpose**: Ingest raw CSV files
- **Execution**: Sequential
- **Total Time**: ~5-10 minutes

### 2. Silver Transformations (Task Group)
- **Purpose**: Clean and transform data to Parquet
- **Execution**: Parallel (9 tasks)
- **Total Time**: ~10-15 minutes (parallel execution)

### 3. dbt Gold Layer (Task Group)
- **Purpose**: Create star schema in PostgreSQL
- **Execution**: Sequential (dependencies between models)
- **Total Time**: ~15-20 minutes

### 4. Data Quality & Reporting
- **Purpose**: Validate and report on data quality
- **Execution**: Sequential
- **Total Time**: ~5 minutes

## Retry Behavior

```
Task Fails
    ↓
Wait 5 minutes (Retry 1)
    ↓
Task Fails Again
    ↓
Wait 10 minutes (Retry 2 - exponential backoff)
    ↓
Task Fails Again
    ↓
Wait 20 minutes (Retry 3 - exponential backoff)
    ↓
Task Fails Again
    ↓
Send Failure Alert Email
    ↓
Mark Task as Failed
```

## Alert Flow

### On Task Failure

```
Task Fails (after all retries)
    ↓
send_failure_alert() callback triggered
    ↓
Generate detailed error email
    ↓
Send to ALERT_EMAIL recipients
    ↓
Write alert JSON to /opt/airflow/logs/alerts/
```

### On DAG Success

```
All tasks complete successfully
    ↓
send_success_alert() callback triggered
    ↓
Generate pipeline summary email
    ↓
Send to ALERT_EMAIL recipients
```

## Data Flow

```
┌──────────────┐
│ Source CSV   │
│ Files (9)    │
└──────┬───────┘
       │
       ▼
┌──────────────┐     ┌──────────────┐
│ Bronze Layer │────▶│  Metadata    │
│ (CSV)        │     │  JSON        │
└──────┬───────┘     └──────────────┘
       │
       ▼
┌──────────────┐     ┌──────────────┐
│ Silver Layer │────▶│ Great        │
│ (Parquet)    │     │ Expectations │
└──────┬───────┘     └──────────────┘
       │
       ▼
┌──────────────┐     ┌──────────────┐
│ Gold Layer   │────▶│ dbt Tests    │
│ (PostgreSQL) │     │              │
└──────┬───────┘     └──────────────┘
       │
       ▼
┌──────────────┐
│ Superset     │
│ Dashboards   │
└──────────────┘
```

## XCom Data Exchange

Tasks share data via XCom:

1. **validate_source_files** → **ingest_bronze_layer**
   - Key: `validated_files`
   - Value: List of validated file paths

2. **ingest_bronze_layer** → **validate_bronze_layer**
   - Key: `bronze_row_counts`
   - Value: Dictionary of {table: row_count}

3. **validate_silver_layer** → **generate_data_quality_report**
   - Key: `silver_validation_result`
   - Value: Great Expectations validation results

4. **validate_gold_layer** → **generate_data_quality_report**
   - Key: `gold_validation_results`
   - Value: Dictionary of {table: row_count}

## Execution Timeline (Expected)

```
Time    Task
00:00   start
00:01   validate_source_files
00:02   ingest_bronze_layer
00:04   validate_bronze_layer
00:05   silver_transformations (parallel)
00:15   validate_silver_layer
00:20   dbt_run_staging
00:25   dbt_test_staging
00:27   dbt_run_dimensions
00:32   dbt_run_facts
00:37   dbt_test_gold
00:42   validate_gold_layer
00:44   generate_data_quality_report
00:45   refresh_superset_cache
00:46   end

Total: ~46 minutes (well under 2-hour timeout)
```

## Resource Usage

### Parallelism
- **Silver Transformations**: 9 parallel tasks
- **Other Stages**: Sequential execution

### Memory
- **Bronze Ingestion**: Low (file copying)
- **Silver Transformation**: Medium (Pandas DataFrames)
- **dbt Models**: Medium (SQL queries)
- **Validation**: Medium (Great Expectations)

### Disk I/O
- **Bronze**: Write CSV files
- **Silver**: Write Parquet files (compressed)
- **Gold**: PostgreSQL inserts/updates

## Monitoring Points

Key metrics to monitor:

1. **Task Duration**: Track execution time trends
2. **Row Counts**: Monitor data volume changes
3. **Validation Success Rate**: Data quality trends
4. **Retry Frequency**: Identify unstable tasks
5. **Disk Usage**: Bronze/Silver layer growth

## Failure Scenarios

### Scenario 1: Missing CSV File
- **Failed Task**: validate_source_files
- **Impact**: Pipeline stops immediately
- **Recovery**: Add missing file and re-run

### Scenario 2: Data Quality Failure
- **Failed Task**: validate_silver_layer
- **Impact**: Pipeline stops before Gold layer
- **Recovery**: Fix data issues and re-run from Silver

### Scenario 3: dbt Test Failure
- **Failed Task**: dbt_test_staging or dbt_test_gold
- **Impact**: Pipeline stops, Gold layer incomplete
- **Recovery**: Fix data or model logic, re-run dbt tasks

### Scenario 4: Database Connection Error
- **Failed Task**: Any dbt task or validate_gold_layer
- **Impact**: Gold layer not updated
- **Recovery**: Fix database connectivity, re-run from dbt_gold_layer

## Best Practices Implemented

✅ Idempotent tasks (can be re-run safely)
✅ Proper error handling and logging
✅ Task timeouts to prevent hung processes
✅ Exponential backoff for retries
✅ Detailed alerting with actionable information
✅ XCom for inter-task communication
✅ Task groups for logical organization
✅ Parallel execution where possible
✅ Sequential execution where dependencies exist
✅ Comprehensive documentation
