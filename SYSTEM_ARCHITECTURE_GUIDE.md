# Healthcare ETL Pipeline - System Architecture Guide

## Table of Contents
1. [System Overview](#system-overview)
2. [File Structure & Functionalities](#file-structure--functionalities)
3. [Data Transformation Pipeline](#data-transformation-pipeline)
4. [Component Deep Dive](#component-deep-dive)
5. [Data Flow Explanation](#data-flow-explanation)
6. [Configuration System](#configuration-system)
7. [Monitoring & Quality Assurance](#monitoring--quality-assurance)
8. [Deployment Architecture](#deployment-architecture)

---

## System Overview

The Healthcare ETL Pipeline is a comprehensive data processing system that implements the **Medallion Architecture** (Bronze/Silver/Gold) using modern data engineering tools. The system automatically processes hospital operational data through multiple layers of transformation and validation.

### Core Architecture Pattern
```
CSV Files → Bronze Layer → Silver Layer → Gold Layer → Analytics
    ↓           ↓            ↓            ↓           ↓
Raw Data → Ingestion → Transformation → Modeling → Visualization
```

### Key Technologies
- **Orchestration**: Apache Airflow (DAG-based workflow management)
- **Transformation**: Python + dbt (SQL-based modeling)
- **Storage**: PostgreSQL (data warehouse) + Parquet files (intermediate)
- **Quality**: Great Expectations (data validation framework)
- **Analytics**: Apache Superset (business intelligence)
- **Deployment**: Docker Compose (containerized services)

---

## File Structure & Functionalities

### Project Root Structure
```
healthcare-etl-pipeline/
├── airflow/                    # Airflow orchestration
│   ├── dags/                  # DAG definitions and Python modules
│   ├── logs/                  # Execution logs
│   └── plugins/               # Custom Airflow plugins
├── config/                    # Configuration files
├── data/                      # Data storage layers
│   ├── bronze/               # Raw ingested data
│   └── silver/               # Cleaned Parquet data
├── dataset/                   # Source CSV files
├── dbt_project/              # dbt models and transformations
├── great_expectations/        # Data quality validation
├── init-scripts/             # Database initialization
├── logs/                     # Application logs
├── superset/                 # Dashboard configurations
├── docker-compose.yml        # Container orchestration
├── requirements.txt          # Python dependencies
└── pipeline-cli.sh          # Management CLI tool
```

### Critical Files and Their Functions

#### 1. Orchestration Layer (`airflow/dags/`)

**`healthcare_etl_dag.py`** - Main DAG Definition
```python
# Primary orchestration file that defines the entire ETL workflow
# Functions:
- Defines 15+ tasks in sequential and parallel execution
- Manages Bronze → Silver → Gold data flow
- Implements retry logic and error handling
- Configures email/Slack alerting
- Sets up task dependencies and scheduling

# Key Components:
- Bronze ingestion tasks
- Silver transformation task group (9 parallel tasks)
- dbt Gold layer transformations
- Data quality validation checkpoints
- Superset cache refresh
```

**`bronze_ingestion.py`** - Bronze Layer Processing
```python
# Handles raw CSV file ingestion
# Functions:
- validate_csv_files(): Checks file existence and basic validation
- ingest_csv_files(): Copies CSV files with timestamps and metadata
- Generates file checksums and row counts
- Creates audit trail for data lineage

# Data Flow:
dataset/*.csv → data/bronze/{run_date}/*.csv + metadata.json
```

**`silver_transformation.py`** - Silver Layer Processing
```python
# Transforms Bronze CSV to Silver Parquet
# Functions:
- transform_bronze_to_silver(): Main transformation orchestrator
- Data type standardization (dates, numbers, strings)
- Deduplication based on primary keys
- Data quality cleaning and validation
- Parquet file generation with compression

# Transformations Applied:
- Date format standardization (DD-MM-YYYY → YYYY-MM-DD)
- Numeric type conversion and validation
- String cleaning and normalization
- Missing value handling
- Audit column addition (load_timestamp, source_file, record_hash)

# Data Flow:
data/bronze/{run_date}/*.csv → data/silver/{run_date}/*.parquet
```

**`data_quality.py`** - Quality Validation Framework
```python
# Great Expectations integration for data validation
# Functions:
- DataQualityValidator class: Main validation orchestrator
- validate_silver_layer(): Runs validation checkpoints
- generate_data_quality_report(): Creates comprehensive reports
- Configurable validation rules and thresholds

# Validation Types:
- Schema validation (column names, types, order)
- Business rule validation (age ranges, date logic)
- Data integrity checks (uniqueness, not null)
- Pattern matching (ID formats, codes)
- Referential integrity (foreign key relationships)
```

#### 2. Data Transformation Layer (`dbt_project/`)

**`dbt_project.yml`** - dbt Configuration
```yaml
# Defines dbt project structure and materialization strategies
# Configurations:
- Model materialization (view, table, incremental)
- Schema organization (staging, dimensions, facts)
- Test configurations and failure handling
- Seed data management
```

**`models/staging/`** - Staging Models (Silver → Staging)
```sql
-- 9 staging models that read from Silver Parquet files
-- Files: stg_patients.sql, stg_encounters.sql, etc.
-- Functions:
- Read from silver schema tables
- Apply basic transformations and cleaning
- Standardize column names and formats
- Add business logic calculations
- Prepare data for dimensional modeling

-- Example: stg_patients.sql
SELECT 
    patient_id,
    UPPER(TRIM(first_name)) as first_name,
    UPPER(TRIM(last_name)) as last_name,
    DATE(dob) as date_of_birth,
    CASE 
        WHEN gender IN ('M', 'Male') THEN 'Male'
        WHEN gender IN ('F', 'Female') THEN 'Female'
        ELSE 'Other'
    END as gender_standardized,
    current_timestamp as dbt_updated_at
FROM {{ source('silver', 'patients') }}
```

**`models/dimensions/`** - Dimension Tables (Staging → Dimensions)
```sql
-- 5 dimension models implementing SCD Type 2
-- Files: dim_patient.sql, dim_provider.sql, etc.
-- Functions:
- Create slowly changing dimensions
- Generate surrogate keys
- Implement effective/expiry date logic
- Handle historical data changes
- Optimize for analytics queries

-- Example: dim_patient.sql creates patient dimension with:
- patient_key (surrogate key)
- patient_id (business key)
- Demographics with SCD Type 2 tracking
- Effective/expiry dates for historical changes
```

**`models/facts/`** - Fact Tables (Staging → Facts)
```sql
-- 4 fact models for transactional data
-- Files: fact_encounter.sql, fact_billing.sql, etc.
-- Functions:
- Create fact tables with foreign keys to dimensions
- Implement incremental loading strategies
- Calculate derived metrics and measures
- Optimize for analytical queries
- Handle late-arriving data

-- Example: fact_encounter.sql creates encounter facts with:
- encounter_key (surrogate key)
- Foreign keys to all relevant dimensions
- Measures (length_of_stay, total_charges)
- Incremental loading based on updated_at
```

#### 3. Configuration System (`config/`)

**`pipeline_config.yaml`** - Master Configuration
```yaml
# Central configuration for entire pipeline
# Sections:
pipeline:          # Pipeline metadata and versioning
bronze:            # Bronze layer settings (paths, validation)
silver:            # Silver layer settings (transformations, Parquet)
gold:              # Gold layer settings (database, dbt)
data_quality:      # Great Expectations configuration
airflow:           # DAG settings, scheduling, alerts
logging:           # Log levels, formats, retention
alerting:          # Email, Slack, PagerDuty settings
performance:       # Benchmarks, monitoring, optimization
```

**`silver_table_config.yaml`** - Table-Specific Transformations
```yaml
# Defines transformation rules for each table
# Structure:
tables:
  patients:
    primary_key: patient_id
    date_columns: [dob]
    numeric_columns: [age]
    categorical_columns: [gender, ethnicity]
    validation_rules:
      age_range: [0, 120]
      required_fields: [patient_id, first_name, last_name]
```

#### 4. Data Quality System (`great_expectations/`)

**`great_expectations.yml`** - GE Configuration
```yaml
# Great Expectations framework configuration
# Defines:
- Data context and store locations
- Validation checkpoints and schedules
- Expectation suites for each table
- Result stores and notification settings
```

**`expectations/`** - Validation Rules
```python
# Expectation suites for each table
# Example: patients_expectations.json
{
  "expectation_suite_name": "patients_suite",
  "expectations": [
    {
      "expectation_type": "expect_column_values_to_not_be_null",
      "kwargs": {"column": "patient_id"}
    },
    {
      "expectation_type": "expect_column_values_to_match_regex",
      "kwargs": {
        "column": "patient_id",
        "regex": "^PAT[0-9]{5}$"
      }
    }
  ]
}
```

#### 5. Infrastructure (`docker-compose.yml`)

**Container Definitions**
```yaml
# Defines 5 main services:
services:
  airflow-webserver:    # Web UI (port 8080)
  airflow-scheduler:    # Task orchestration
  postgres:             # Airflow metadata (port 5432)
  warehouse-db:         # Data warehouse (port 5433)
  superset:            # Analytics platform (port 8088)

# Volume mappings for data persistence:
- ./airflow/dags → /opt/airflow/dags
- ./data → /opt/airflow/data
- ./dbt_project → /opt/airflow/dbt_project
```

---

## Data Transformation Pipeline

### Phase 1: Bronze Layer (Raw Ingestion)
**Location**: `airflow/dags/bronze_ingestion.py`

```python
def ingest_csv_files(source_dir, bronze_dir, run_date):
    """
    Raw CSV ingestion with metadata generation
    
    Process:
    1. Scan dataset/ directory for CSV files
    2. Validate file existence and basic structure
    3. Copy files to data/bronze/{run_date}/ with timestamps
    4. Generate metadata.json with file statistics
    5. Calculate checksums for data integrity
    6. Log row counts and file sizes
    
    Input:  dataset/*.csv
    Output: data/bronze/{run_date}/*.csv + _metadata.json
    """
```

**Transformations Applied**:
- **None** - Bronze layer preserves raw data exactly as received
- **Metadata Addition**: Timestamps, checksums, row counts
- **File Organization**: Date-partitioned directory structure
- **Audit Trail**: Complete lineage tracking

### Phase 2: Silver Layer (Data Cleaning)
**Location**: `airflow/dags/silver_transformation.py`

```python
def transform_bronze_to_silver(bronze_dir, silver_dir, config_file, run_date, table_name):
    """
    Clean and standardize data for analytics
    
    Process:
    1. Read CSV from Bronze layer
    2. Apply table-specific transformation rules
    3. Standardize data types and formats
    4. Handle missing values and duplicates
    5. Add audit columns
    6. Save as compressed Parquet files
    
    Input:  data/bronze/{run_date}/*.csv
    Output: data/silver/{run_date}/*.parquet
    """
```

**Transformations Applied**:
```python
# Date Standardization
source_format = "%d-%m-%Y"      # Input: 15-03-2024
target_format = "%Y-%m-%d"      # Output: 2024-03-15

# Data Type Conversion
age = pd.to_numeric(age, errors='coerce')           # String → Integer
admission_date = pd.to_datetime(date_col)           # String → DateTime
cost = pd.to_numeric(cost, errors='coerce')         # String → Float

# Data Cleaning
first_name = first_name.str.strip().str.title()    # Normalize names
gender = gender.map({'M': 'Male', 'F': 'Female'})  # Standardize values

# Deduplication
df = df.drop_duplicates(subset=['patient_id'], keep='first')

# Audit Columns
df['load_timestamp'] = datetime.now()
df['source_file'] = source_file_path
df['record_hash'] = df.apply(lambda x: hashlib.md5(str(x).encode()).hexdigest(), axis=1)
```

### Phase 3: Warehouse Loading
**Location**: `airflow/dags/healthcare_etl_dag.py` (load_silver_to_warehouse function)

```python
def load_silver_to_warehouse():
    """
    Load Parquet files to PostgreSQL warehouse
    
    Process:
    1. Connect to PostgreSQL warehouse database
    2. Create 'silver' schema if not exists
    3. Read Parquet files from Silver layer
    4. Truncate existing tables (for full refresh)
    5. Load data using pandas.to_sql()
    6. Create indexes for performance
    
    Input:  data/silver/{run_date}/*.parquet
    Output: PostgreSQL silver schema tables
    """
```

### Phase 4: Gold Layer (dbt Transformations)
**Location**: `dbt_project/models/`

#### Staging Models (`models/staging/`)
```sql
-- stg_patients.sql
-- Purpose: Clean and prepare patient data for dimensional modeling

{{ config(materialized='view') }}

SELECT 
    -- Business Keys
    patient_id,
    
    -- Demographics (cleaned and standardized)
    TRIM(UPPER(first_name)) as first_name,
    TRIM(UPPER(last_name)) as last_name,
    DATE(dob) as date_of_birth,
    EXTRACT(YEAR FROM AGE(DATE(dob))) as current_age,
    
    -- Standardized categorical values
    CASE 
        WHEN UPPER(gender) IN ('M', 'MALE') THEN 'Male'
        WHEN UPPER(gender) IN ('F', 'FEMALE') THEN 'Female'
        ELSE 'Other'
    END as gender_standardized,
    
    CASE 
        WHEN UPPER(ethnicity) = 'HISPANIC' THEN 'Hispanic/Latino'
        WHEN UPPER(ethnicity) = 'WHITE' THEN 'White'
        WHEN UPPER(ethnicity) = 'BLACK' THEN 'Black/African American'
        ELSE 'Other/Unknown'
    END as ethnicity_standardized,
    
    -- Insurance information
    insurance_type,
    
    -- Contact information (masked for privacy)
    CASE 
        WHEN LENGTH(phone) = 10 THEN 
            CONCAT('(', SUBSTR(phone, 1, 3), ') ', SUBSTR(phone, 4, 3), '-', SUBSTR(phone, 7, 4))
        ELSE phone
    END as phone_formatted,
    
    -- Audit fields
    load_timestamp,
    source_file,
    current_timestamp as dbt_updated_at

FROM {{ source('silver', 'patients') }}
WHERE patient_id IS NOT NULL
```

#### Dimension Models (`models/dimensions/`)
```sql
-- dim_patient.sql
-- Purpose: Create patient dimension with SCD Type 2 for historical tracking

{{ config(
    materialized='table',
    unique_key='patient_key'
) }}

WITH source_data AS (
    SELECT * FROM {{ ref('stg_patients') }}
),

-- Generate surrogate keys
with_keys AS (
    SELECT 
        {{ dbt_utils.generate_surrogate_key(['patient_id', 'dbt_updated_at']) }} as patient_key,
        *
    FROM source_data
),

-- Implement SCD Type 2 logic
final AS (
    SELECT 
        patient_key,
        patient_id,
        first_name,
        last_name,
        date_of_birth,
        current_age,
        gender_standardized as gender,
        ethnicity_standardized as ethnicity,
        insurance_type,
        phone_formatted as phone,
        
        -- SCD Type 2 fields
        dbt_updated_at as effective_date,
        LEAD(dbt_updated_at, 1, '9999-12-31'::date) 
            OVER (PARTITION BY patient_id ORDER BY dbt_updated_at) as expiry_date,
        CASE 
            WHEN LEAD(dbt_updated_at, 1) OVER (PARTITION BY patient_id ORDER BY dbt_updated_at) IS NULL 
            THEN TRUE 
            ELSE FALSE 
        END as is_current,
        
        -- Audit fields
        current_timestamp as created_at,
        current_timestamp as updated_at
        
    FROM with_keys
)

SELECT * FROM final
```

#### Fact Models (`models/facts/`)
```sql
-- fact_encounter.sql
-- Purpose: Create encounter fact table with all relevant measures

{{ config(
    materialized='incremental',
    unique_key='encounter_key',
    on_schema_change='fail'
) }}

WITH encounters AS (
    SELECT * FROM {{ ref('stg_encounters') }}
),

-- Join with dimensions to get surrogate keys
with_dimension_keys AS (
    SELECT 
        e.*,
        p.patient_key,
        pr.provider_key,
        dd.date_key as admission_date_key,
        dd2.date_key as discharge_date_key
    FROM encounters e
    LEFT JOIN {{ ref('dim_patient') }} p 
        ON e.patient_id = p.patient_id 
        AND p.is_current = TRUE
    LEFT JOIN {{ ref('dim_provider') }} pr 
        ON e.provider_id = pr.provider_id 
        AND pr.is_current = TRUE
    LEFT JOIN {{ ref('dim_date') }} dd 
        ON DATE(e.admission_date) = dd.full_date
    LEFT JOIN {{ ref('dim_date') }} dd2 
        ON DATE(e.discharge_date) = dd2.full_date
),

-- Calculate derived measures
final AS (
    SELECT 
        {{ dbt_utils.generate_surrogate_key(['encounter_id']) }} as encounter_key,
        encounter_id,
        
        -- Foreign keys to dimensions
        patient_key,
        provider_key,
        admission_date_key,
        discharge_date_key,
        
        -- Encounter details
        encounter_type,
        department,
        admission_date,
        discharge_date,
        
        -- Calculated measures
        CASE 
            WHEN discharge_date IS NOT NULL 
            THEN DATE_PART('day', discharge_date - admission_date)
            ELSE NULL
        END as length_of_stay_days,
        
        COALESCE(total_charges, 0) as total_charges,
        
        discharge_status,
        
        -- Audit fields
        load_timestamp,
        current_timestamp as dbt_updated_at
        
    FROM with_dimension_keys
)

SELECT * FROM final

{% if is_incremental() %}
    WHERE dbt_updated_at > (SELECT MAX(dbt_updated_at) FROM {{ this }})
{% endif %}
```

---

## Component Deep Dive

### 1. Airflow Orchestration Engine

**Core Components**:
```python
# DAG Definition (healthcare_etl_dag.py)
dag = DAG(
    'healthcare_etl_pipeline',
    schedule_interval='0 2 * * *',  # Daily at 2 AM UTC
    max_active_runs=1,              # Prevent concurrent runs
    catchup=False,                  # Don't backfill
    tags=['healthcare', 'etl']
)

# Task Dependencies
start >> validate_source >> ingest_bronze >> validate_bronze >> silver_group >> validate_silver >> load_warehouse >> dbt_group >> validate_gold >> generate_report >> refresh_superset >> end
```

**Task Groups**:
```python
# Silver Transformations (Parallel Processing)
with TaskGroup('silver_transformations') as silver_group:
    for table in TABLE_NAMES:
        PythonOperator(
            task_id=f'transform_{table}',
            python_callable=transform_table_to_silver,
            op_kwargs={'table_name': table}
        )

# dbt Gold Layer (Sequential Processing)
with TaskGroup('dbt_gold_layer') as dbt_group:
    dbt_deps >> dbt_run_staging >> dbt_test_staging >> dbt_run_dimensions >> dbt_run_facts >> dbt_test_gold
```

### 2. Data Quality Framework

**Great Expectations Integration**:
```python
class DataQualityValidator:
    def __init__(self, context_root_dir):
        self.context = DataContext(context_root_dir)
    
    def validate_silver_layer(self, run_date):
        """Run validation checkpoint for Silver layer"""
        checkpoint = self.context.get_checkpoint("silver_validation_checkpoint")
        results = checkpoint.run()
        return self._process_validation_results(results)
    
    def _process_validation_results(self, results):
        """Process and summarize validation results"""
        return {
            'success': results.success,
            'statistics': {
                'evaluated_validations': len(results.run_results),
                'successful_validations': sum(1 for r in results.run_results if r.success),
                'unsuccessful_validations': sum(1 for r in results.run_results if not r.success),
                'success_percent': (successful / total) * 100
            }
        }
```

**Validation Rules Examples**:
```python
# Schema Validation
expect_table_columns_to_match_ordered_list(
    column_list=['patient_id', 'first_name', 'last_name', 'dob', 'gender']
)

# Business Rules
expect_column_values_to_be_between(
    column='age', 
    min_value=0, 
    max_value=120
)

# Pattern Matching
expect_column_values_to_match_regex(
    column='patient_id',
    regex='^PAT[0-9]{5}$'
)

# Referential Integrity
expect_column_values_to_be_in_set(
    column='gender',
    value_set=['Male', 'Female', 'Other']
)
```

### 3. dbt Transformation Engine

**Model Materialization Strategies**:
```yaml
# dbt_project.yml
models:
  healthcare_etl:
    staging:
      +materialized: view        # Fast, no storage overhead
    dimensions:
      +materialized: table       # Persistent, optimized for joins
    facts:
      +materialized: incremental # Only process new/changed data
      +unique_key: 'encounter_id'
```

**Incremental Loading Logic**:
```sql
-- fact_encounter.sql
SELECT * FROM source_data
{% if is_incremental() %}
    WHERE updated_at > (SELECT MAX(updated_at) FROM {{ this }})
{% endif %}
```

**Testing Framework**:
```yaml
# models/schema.yml
models:
  - name: dim_patient
    tests:
      - unique:
          column_name: patient_key
      - not_null:
          column_name: patient_key
    columns:
      - name: patient_id
        tests:
          - not_null
          - relationships:
              to: ref('stg_patients')
              field: patient_id
```

---

## Data Flow Explanation

### Complete Data Journey

#### Step 1: Source Data Arrival
```
Location: dataset/
Files: patients.csv, encounters.csv, diagnoses.csv, etc.
Format: CSV with headers
Validation: File existence, basic structure
```

#### Step 2: Bronze Layer Ingestion
```python
# Process: bronze_ingestion.py
Source: dataset/*.csv
Target: data/bronze/{run_date}/*.csv

# Transformations:
- File copying with timestamp preservation
- Metadata generation (row counts, checksums)
- Directory organization by run date
- Audit trail creation

# Output Structure:
data/bronze/2024-01-15/
├── patients.csv
├── encounters.csv
├── diagnoses.csv
└── _metadata.json
```

#### Step 3: Silver Layer Transformation
```python
# Process: silver_transformation.py
Source: data/bronze/{run_date}/*.csv
Target: data/silver/{run_date}/*.parquet

# Transformations per table:
patients.csv → patients.parquet:
- Date format: 15-03-1990 → 1990-03-15
- Name cleaning: "john doe" → "John Doe"
- Gender standardization: "M" → "Male"
- Phone formatting: "1234567890" → "(123) 456-7890"
- Deduplication by patient_id
- Audit columns: load_timestamp, source_file, record_hash

encounters.csv → encounters.parquet:
- Date standardization for admission/discharge dates
- Length of stay calculation
- Department code standardization
- Charge amount validation and formatting
- Foreign key validation (patient_id exists)
```

#### Step 4: Warehouse Loading
```python
# Process: load_silver_to_warehouse()
Source: data/silver/{run_date}/*.parquet
Target: PostgreSQL silver schema

# Database Operations:
1. CREATE SCHEMA IF NOT EXISTS silver
2. For each parquet file:
   - TRUNCATE TABLE silver.{table_name}
   - INSERT data using pandas.to_sql()
   - CREATE INDEX on primary keys
3. ANALYZE tables for query optimization
```

#### Step 5: dbt Gold Layer Processing
```sql
-- Stage 1: Staging Models (silver → staging views)
CREATE VIEW staging.stg_patients AS
SELECT 
    patient_id,
    TRIM(UPPER(first_name)) as first_name,
    -- Additional cleaning and standardization
FROM silver.patients;

-- Stage 2: Dimension Models (staging → dimension tables)
CREATE TABLE public.dim_patient AS
SELECT 
    {{ generate_surrogate_key(['patient_id']) }} as patient_key,
    patient_id,
    first_name,
    last_name,
    -- SCD Type 2 implementation
    effective_date,
    expiry_date,
    is_current
FROM staging.stg_patients;

-- Stage 3: Fact Models (staging + dimensions → fact tables)
CREATE TABLE public.fact_encounter AS
SELECT 
    {{ generate_surrogate_key(['encounter_id']) }} as encounter_key,
    encounter_id,
    p.patient_key,  -- Foreign key from dimension
    pr.provider_key, -- Foreign key from dimension
    admission_date,
    discharge_date,
    length_of_stay_days,
    total_charges
FROM staging.stg_encounters e
JOIN public.dim_patient p ON e.patient_id = p.patient_id AND p.is_current
JOIN public.dim_provider pr ON e.provider_id = pr.provider_id AND pr.is_current;
```

#### Step 6: Data Quality Validation
```python
# Great Expectations validation at each layer
Bronze Validation:
- File existence and row count checks
- Basic structure validation

Silver Validation:
- Schema validation (column names, types)
- Business rule validation (age ranges, date logic)
- Data quality checks (uniqueness, completeness)
- Pattern matching (ID formats)

Gold Validation:
- Referential integrity checks
- Aggregate validation (row counts match expectations)
- Business metric validation
```

#### Step 7: Analytics Layer
```python
# Superset dashboard data sources
Data Sources:
- dim_patient: Patient demographics and attributes
- dim_provider: Healthcare professional information
- fact_encounter: Hospital visits and stays
- fact_billing: Financial transactions
- fact_lab_test: Laboratory results

Dashboard Categories:
1. Operational: Patient flow, bed utilization, department volumes
2. Financial: Revenue, payments, denials, collection rates
3. Clinical: Diagnoses, procedures, readmissions, quality metrics
4. Quality: Data pipeline health, validation results
```

---

## Configuration System

### Environment-Based Configuration

#### Development Environment
```yaml
# .env (development)
ENVIRONMENT=development
POSTGRES_HOST=warehouse-db
POSTGRES_PORT=5432
DATA_QUALITY_FAIL_ON_ERROR=false
AIRFLOW_DAG_SCHEDULE=null  # Manual trigger only

# Behavior:
- Verbose logging (DEBUG level)
- Data quality failures don't stop pipeline
- Manual DAG triggering
- Smaller dataset processing
```

#### Production Environment
```yaml
# .env (production)
ENVIRONMENT=production
POSTGRES_HOST=prod-warehouse.company.com
POSTGRES_PORT=5432
DATA_QUALITY_FAIL_ON_ERROR=true
AIRFLOW_DAG_SCHEDULE="0 2 * * *"  # Daily at 2 AM

# Behavior:
- Error-level logging only
- Data quality failures stop pipeline
- Automated scheduling
- Full dataset processing
- Comprehensive alerting
```

### Configuration Hierarchy
```
1. Environment Variables (.env)
2. Pipeline Config (config/pipeline_config.yaml)
3. Table-Specific Config (config/silver_table_config.yaml)
4. dbt Profiles (dbt_project/profiles.yml)
5. Great Expectations Config (great_expectations/great_expectations.yml)
```

---

## Monitoring & Quality Assurance

### Multi-Layer Monitoring

#### 1. Infrastructure Monitoring
```yaml
# Docker health checks
Services:
  postgres: pg_isready -U airflow
  warehouse-db: pg_isready -U etl_user -d healthcare_warehouse
  airflow-webserver: curl http://localhost:8080/health
  superset: curl http://localhost:8088/health

# Resource monitoring
Metrics:
  - CPU usage per container
  - Memory consumption
  - Disk I/O rates
  - Network traffic
```

#### 2. Pipeline Monitoring
```python
# Airflow task monitoring
Metrics Tracked:
- Task execution duration
- Success/failure rates
- Retry attempts
- Queue wait times
- Resource utilization

# Custom metrics in DAG
def track_execution_metrics(context):
    task_instance = context['task_instance']
    duration = task_instance.end_date - task_instance.start_date
    
    # Log metrics
    logger.info(f"Task {task_instance.task_id} completed in {duration}")
    
    # Send to monitoring system
    send_metric('task_duration', duration.total_seconds(), 
                tags={'task_id': task_instance.task_id})
```

#### 3. Data Quality Monitoring
```python
# Great Expectations monitoring
Quality Metrics:
- Validation success rates
- Failed expectation counts
- Data drift detection
- Anomaly identification

# Quality score calculation
def calculate_quality_score(validation_results):
    total_expectations = len(validation_results)
    successful_expectations = sum(1 for r in validation_results if r.success)
    return (successful_expectations / total_expectations) * 100
```

#### 4. Business Metrics Monitoring
```sql
-- dbt tests for business logic
-- tests/assert_encounter_dates_logical.sql
SELECT *
FROM {{ ref('fact_encounter') }}
WHERE discharge_date < admission_date
  OR length_of_stay_days < 0
  OR length_of_stay_days > 365

-- tests/assert_patient_age_reasonable.sql
SELECT *
FROM {{ ref('dim_patient') }}
WHERE current_age < 0 
  OR current_age > 120
```

### Alerting System

#### Alert Channels
```python
# Email alerts
def send_email_alert(context, alert_type):
    subject = f"[{alert_type}] Healthcare ETL Pipeline Alert"
    html_content = f"""
    <h2>Pipeline Alert</h2>
    <p><strong>DAG:</strong> {context['dag'].dag_id}</p>
    <p><strong>Task:</strong> {context['task_instance'].task_id}</p>
    <p><strong>Status:</strong> {alert_type}</p>
    <p><strong>Execution Date:</strong> {context['execution_date']}</p>
    """
    send_email(to=ALERT_EMAIL, subject=subject, html_content=html_content)

# Slack alerts
def send_slack_alert(message, channel='#data-alerts'):
    webhook_url = os.getenv('SLACK_WEBHOOK_URL')
    payload = {
        'channel': channel,
        'text': message,
        'username': 'Healthcare ETL Bot'
    }
    requests.post(webhook_url, json=payload)
```

#### Alert Severity Levels
```python
ALERT_LEVELS = {
    'CRITICAL': {
        'conditions': ['pipeline_failure', 'data_corruption', 'database_down'],
        'actions': ['email', 'slack', 'pagerduty'],
        'escalation': True
    },
    'WARNING': {
        'conditions': ['data_quality_failure', 'performance_degradation'],
        'actions': ['email', 'slack'],
        'escalation': False
    },
    'INFO': {
        'conditions': ['pipeline_success', 'validation_passed'],
        'actions': ['log'],
        'escalation': False
    }
}
```

---

## Deployment Architecture

### Container Orchestration

#### Service Dependencies
```yaml
# docker-compose.yml service startup order
1. postgres (Airflow metadata)
2. warehouse-db (Data warehouse)
3. airflow-init (One-time setup)
4. airflow-scheduler (Background orchestration)
5. airflow-webserver (Web UI)
6. superset (Analytics platform)
```

#### Volume Management
```yaml
# Persistent data volumes
volumes:
  postgres-db-volume:     # Airflow metadata persistence
  warehouse-db-volume:    # Data warehouse persistence
  superset-volume:        # Superset configuration persistence

# Shared application volumes
./airflow/dags → /opt/airflow/dags           # DAG definitions
./data → /opt/airflow/data                   # Data layers (Bronze/Silver)
./dbt_project → /opt/airflow/dbt_project     # dbt models
./config → /opt/airflow/config               # Configuration files
```

#### Network Configuration
```yaml
# Internal service communication
networks:
  healthcare-etl-network:
    driver: bridge
    
# Service resolution
airflow-webserver → postgres:5432 (metadata)
airflow-webserver → warehouse-db:5432 (data)
superset → warehouse-db:5432 (analytics)
```

### Scaling Considerations

#### Horizontal Scaling
```yaml
# Multiple Airflow workers
services:
  airflow-worker-1:
    <<: *airflow-common
    command: celery worker
  airflow-worker-2:
    <<: *airflow-common
    command: celery worker
    
# Load balancer for web UI
nginx:
  image: nginx
  ports:
    - "80:80"
  depends_on:
    - airflow-webserver-1
    - airflow-webserver-2
```

#### Vertical Scaling
```yaml
# Resource allocation
services:
  warehouse-db:
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
        reservations:
          memory: 2G
          cpus: '1.0'
```

This comprehensive guide explains how every component of the Healthcare ETL Pipeline works together, from raw CSV ingestion through to analytics-ready dimensional models. The system implements modern data engineering best practices with robust monitoring, quality assurance, and scalable architecture.