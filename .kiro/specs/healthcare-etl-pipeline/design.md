# Healthcare ETL Pipeline - Design Document

## Overview

This design implements a production-grade ETL pipeline for hospital operational data using Apache Airflow orchestration, medallion architecture (Bronze/Silver/Gold), and modern data engineering best practices. The pipeline processes 126,000+ rows across 9 healthcare tables, implementing data quality checks, star schema modeling, and analytics visualization.

### Architecture Principles

- **Medallion Architecture**: Progressive data refinement through Bronze (raw) → Silver (cleaned) → Gold (analytics-ready) layers
- **Idempotency**: All pipeline operations can be safely re-run without side effects
- **Incremental Processing**: Optimize performance by processing only new/changed data where applicable
- **Data Quality First**: Validate data at each layer before promotion
- **Separation of Concerns**: Extract, transform, and load operations are isolated and testable

## Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Apache Airflow                            │
│                     (Orchestration Layer)                        │
└────────────┬────────────────────────────────────┬───────────────┘
             │                                     │
             ▼                                     ▼
┌────────────────────────┐            ┌──────────────────────────┐
│   Bronze Layer         │            │  Great Expectations      │
│   (Raw CSV Files)      │───────────▶│  (Data Quality Engine)   │
│   - Immutable source   │            └──────────────────────────┘
└────────────┬───────────┘                        │
             │                                     │
             ▼                                     ▼
┌────────────────────────┐            ┌──────────────────────────┐
│   Silver Layer         │            │   Quality Reports        │
│   (Parquet Files)      │◀───────────│   & Alerts               │
│   - Cleaned data       │            └──────────────────────────┘
│   - Type validation    │
└────────────┬───────────┘
             │
             ▼
┌────────────────────────┐
│   dbt Transformations  │
│   - Business logic     │
│   - Tests & docs       │
└────────────┬───────────┘
             │
             ▼
┌────────────────────────┐            ┌──────────────────────────┐
│   Gold Layer           │            │   Apache Superset        │
│   (PostgreSQL)         │───────────▶│   (Visualization)        │
│   - Star schema        │            │   - Dashboards           │
│   - Dim/Fact tables    │            │   - Analytics            │
└────────────────────────┘            └──────────────────────────┘
```

### Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Orchestration | Apache Airflow 2.8+ | Workflow scheduling and monitoring |
| Transformation | Pandas | Data cleaning and Silver layer processing |
| Modeling | dbt Core | Gold layer transformations and testing |
| Data Quality | Great Expectations | Validation and quality checks |
| Warehouse | PostgreSQL 15+ | Analytics database (Gold layer) |
| Visualization | Apache Superset | Dashboards and reporting |
| Storage | Local filesystem | Bronze/Silver layer storage |

**Note**: PySpark, BigQuery, Kafka, and MLflow are excluded from this design as they introduce unnecessary complexity for the 126K row dataset. The chosen stack is simpler, faster to implement, and sufficient for the requirements.

## Components and Interfaces

### 1. Bronze Layer (Raw Data Ingestion)

**Purpose**: Store immutable raw CSV files as the source of truth

**Implementation**:
- Directory structure: `data/bronze/YYYY-MM-DD/`
- Files copied with timestamp prefix: `2025-01-15_patients.csv`
- No transformations applied
- Metadata file created: `_metadata.json` with row counts and checksums

**Interface**:
```python
class BronzeIngestion:
    def ingest_csv_files(source_dir: str, bronze_dir: str, run_date: str) -> Dict[str, int]:
        """
        Copy CSV files to Bronze layer with metadata
        Returns: {filename: row_count}
        """
```

### 2. Silver Layer (Data Cleaning)

**Purpose**: Clean, validate, and standardize data in Parquet format

**Transformations Applied**:

1. **Date Standardization**:
   - Convert all date formats (DD-MM-YYYY) to ISO 8601 (YYYY-MM-DD)
   - Parse datetime fields with timezone awareness

2. **Data Type Conversion**:
   - patient_id, encounter_id, provider_id → string
   - age, length_of_stay, years_experience → integer
   - costs, amounts → decimal(10,2)
   - dates → date type

3. **Missing Data Handling**:
   - Phone numbers: Fill with 'NOT_PROVIDED'
   - Email: Fill with 'NOT_PROVIDED'
   - Numeric fields: Keep as NULL (do not impute)
   - Categorical fields: Fill with 'UNKNOWN'

4. **Deduplication**:
   - Remove exact duplicates based on primary key
   - Keep first occurrence for duplicates

5. **Audit Columns**:
   - `load_timestamp`: Pipeline execution timestamp
   - `source_file`: Original CSV filename
   - `record_hash`: MD5 hash for change detection

**Directory Structure**: `data/silver/YYYY-MM-DD/table_name.parquet`

**Interface**:
```python
class SilverTransformation:
    def transform_table(
        bronze_file: str,
        silver_dir: str,
        table_config: Dict
    ) -> pd.DataFrame:
        """
        Clean and transform Bronze data to Silver Parquet
        Returns: Transformed DataFrame
        """
```

### 3. Data Quality Validation

**Purpose**: Validate data integrity using Great Expectations

**Validation Suites**:

**Bronze → Silver Validation**:
- Row count matches source file
- No completely empty rows
- Primary keys are unique and not null
- File format is valid

**Silver Layer Validation**:
- Schema validation (column names, types)
- Primary key uniqueness
- Referential integrity (foreign keys exist)
- Value range checks (age 0-120, costs >= 0)
- Date logic (admission_date <= discharge_date)
- Pattern matching (IDs follow format)
- Null checks on required fields

**Gold Layer Validation**:
- Dimension table uniqueness
- Fact table foreign key validity
- Aggregate consistency checks
- No orphaned records

**Interface**:
```python
class DataQualityValidator:
    def validate_silver_table(
        df: pd.DataFrame,
        table_name: str,
        expectation_suite: str
    ) -> ValidationResult:
        """
        Run Great Expectations validation suite
        Returns: ValidationResult with success/failure details
        """
```

### 4. Gold Layer - Star Schema Design

**Purpose**: Create analytics-ready dimensional model

#### Dimension Tables

**dim_patient**:
```sql
CREATE TABLE dim_patient (
    patient_key SERIAL PRIMARY KEY,
    patient_id VARCHAR(20) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    dob DATE,
    age INTEGER,
    gender VARCHAR(20),
    ethnicity VARCHAR(50),
    insurance_type VARCHAR(50),
    marital_status VARCHAR(50),
    city VARCHAR(100),
    state VARCHAR(2),
    zip VARCHAR(10),
    email VARCHAR(200),
    -- SCD Type 2 columns
    valid_from DATE NOT NULL,
    valid_to DATE,
    is_current BOOLEAN DEFAULT TRUE,
    -- Audit columns
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_patient_id ON dim_patient(patient_id);
CREATE INDEX idx_patient_current ON dim_patient(is_current);
```

**dim_provider**:
```sql
CREATE TABLE dim_provider (
    provider_key SERIAL PRIMARY KEY,
    provider_id VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(200),
    department VARCHAR(100),
    specialty VARCHAR(100),
    npi VARCHAR(20),
    inhouse BOOLEAN,
    location VARCHAR(50),
    years_experience INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**dim_date**:
```sql
CREATE TABLE dim_date (
    date_key INTEGER PRIMARY KEY,
    date DATE UNIQUE NOT NULL,
    year INTEGER,
    quarter INTEGER,
    month INTEGER,
    month_name VARCHAR(20),
    week INTEGER,
    day_of_month INTEGER,
    day_of_week INTEGER,
    day_name VARCHAR(20),
    is_weekend BOOLEAN,
    is_holiday BOOLEAN
);
```

**dim_diagnosis**:
```sql
CREATE TABLE dim_diagnosis (
    diagnosis_key SERIAL PRIMARY KEY,
    diagnosis_code VARCHAR(20) UNIQUE NOT NULL,
    diagnosis_description TEXT,
    is_chronic BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**dim_procedure**:
```sql
CREATE TABLE dim_procedure (
    procedure_key SERIAL PRIMARY KEY,
    procedure_code VARCHAR(20) UNIQUE NOT NULL,
    procedure_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**dim_medication**:
```sql
CREATE TABLE dim_medication (
    medication_key SERIAL PRIMARY KEY,
    drug_name VARCHAR(200) NOT NULL,
    dosage VARCHAR(50),
    route VARCHAR(50),
    frequency VARCHAR(100),
    UNIQUE(drug_name, dosage, route),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Fact Tables

**fact_encounter**:
```sql
CREATE TABLE fact_encounter (
    encounter_key SERIAL PRIMARY KEY,
    encounter_id VARCHAR(20) UNIQUE NOT NULL,
    patient_key INTEGER REFERENCES dim_patient(patient_key),
    provider_key INTEGER REFERENCES dim_provider(provider_key),
    visit_date_key INTEGER REFERENCES dim_date(date_key),
    discharge_date_key INTEGER REFERENCES dim_date(date_key),
    diagnosis_key INTEGER REFERENCES dim_diagnosis(diagnosis_key),
    -- Denormalized attributes
    visit_type VARCHAR(50),
    department VARCHAR(100),
    admission_type VARCHAR(50),
    length_of_stay INTEGER,
    status VARCHAR(50),
    readmitted_flag BOOLEAN,
    -- Metrics
    total_procedures INTEGER DEFAULT 0,
    total_medications INTEGER DEFAULT 0,
    total_lab_tests INTEGER DEFAULT 0,
    total_cost DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_encounter_patient ON fact_encounter(patient_key);
CREATE INDEX idx_encounter_provider ON fact_encounter(provider_key);
CREATE INDEX idx_encounter_visit_date ON fact_encounter(visit_date_key);
```

**fact_billing**:
```sql
CREATE TABLE fact_billing (
    billing_key SERIAL PRIMARY KEY,
    billing_id VARCHAR(20) UNIQUE NOT NULL,
    encounter_key INTEGER REFERENCES fact_encounter(encounter_key),
    patient_key INTEGER REFERENCES dim_patient(patient_key),
    claim_billing_date_key INTEGER REFERENCES dim_date(date_key),
    -- Denormalized attributes
    insurance_provider VARCHAR(100),
    payment_method VARCHAR(50),
    claim_status VARCHAR(50),
    denial_reason VARCHAR(200),
    -- Metrics
    billed_amount DECIMAL(10,2),
    paid_amount DECIMAL(10,2),
    denied_amount DECIMAL(10,2),
    payment_rate DECIMAL(5,2), -- paid/billed percentage
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_billing_encounter ON fact_billing(encounter_key);
CREATE INDEX idx_billing_date ON fact_billing(claim_billing_date_key);
```

**fact_lab_test**:
```sql
CREATE TABLE fact_lab_test (
    lab_test_key SERIAL PRIMARY KEY,
    lab_id VARCHAR(20),
    encounter_key INTEGER REFERENCES fact_encounter(encounter_key),
    test_date_key INTEGER REFERENCES dim_date(date_key),
    test_name VARCHAR(200),
    test_code VARCHAR(50),
    specimen_type VARCHAR(100),
    test_result VARCHAR(50),
    status VARCHAR(50),
    is_abnormal BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_lab_encounter ON fact_lab_test(encounter_key);
```

**fact_denial**:
```sql
CREATE TABLE fact_denial (
    denial_key SERIAL PRIMARY KEY,
    denial_id VARCHAR(20) UNIQUE NOT NULL,
    billing_key INTEGER REFERENCES fact_billing(billing_key),
    denial_date_key INTEGER REFERENCES dim_date(date_key),
    appeal_resolution_date_key INTEGER REFERENCES dim_date(date_key),
    denial_reason_code VARCHAR(20),
    denial_reason_description TEXT,
    denied_amount DECIMAL(10,2),
    appeal_filed BOOLEAN,
    appeal_status VARCHAR(50),
    final_outcome VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_denial_billing ON fact_denial(billing_key);
```

### 5. dbt Models Structure

**Directory Structure**:
```
dbt_project/
├── models/
│   ├── staging/
│   │   ├── stg_patients.sql
│   │   ├── stg_encounters.sql
│   │   ├── stg_diagnoses.sql
│   │   ├── stg_procedures.sql
│   │   ├── stg_medications.sql
│   │   ├── stg_lab_tests.sql
│   │   ├── stg_claims_billing.sql
│   │   ├── stg_providers.sql
│   │   └── stg_denials.sql
│   ├── dimensions/
│   │   ├── dim_patient.sql
│   │   ├── dim_provider.sql
│   │   ├── dim_date.sql
│   │   ├── dim_diagnosis.sql
│   │   ├── dim_procedure.sql
│   │   └── dim_medication.sql
│   └── facts/
│       ├── fact_encounter.sql
│       ├── fact_billing.sql
│       ├── fact_lab_test.sql
│       └── fact_denial.sql
├── tests/
│   ├── assert_referential_integrity.sql
│   └── assert_no_orphaned_records.sql
└── dbt_project.yml
```

**dbt Model Strategy**:
- **Staging models**: Read from Silver Parquet files, minimal transformation
- **Dimension models**: Create surrogate keys, implement SCD Type 2 for dim_patient
- **Fact models**: Join staging models, create foreign keys, calculate metrics
- **Incremental strategy**: Use `incremental` materialization for fact tables with `unique_key`

### 6. Airflow DAG Design

**DAG Structure**:

```python
# healthcare_etl_dag.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'email': ['alerts@hospital.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'retry_exponential_backoff': True,
    'max_retry_delay': timedelta(minutes=30),
}

dag = DAG(
    'healthcare_etl_pipeline',
    default_args=default_args,
    description='Hospital data ETL with Bronze/Silver/Gold layers',
    schedule_interval='0 2 * * *',  # Daily at 2 AM UTC
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['healthcare', 'etl', 'production'],
)
```

**Task Dependencies**:

```
start
  │
  ├─> bronze_ingest_patients ─┐
  ├─> bronze_ingest_encounters ─┤
  ├─> bronze_ingest_diagnoses ─┤
  ├─> bronze_ingest_procedures ─┤
  ├─> bronze_ingest_medications ─┤
  ├─> bronze_ingest_lab_tests ─┤
  ├─> bronze_ingest_claims ─┤
  ├─> bronze_ingest_providers ─┤
  └─> bronze_ingest_denials ─┘
                              │
                              ▼
                    validate_bronze_layer
                              │
  ┌───────────────────────────┴───────────────────────────┐
  │                                                         │
  ├─> silver_transform_patients ─┐                         │
  ├─> silver_transform_encounters ─┤                       │
  ├─> silver_transform_diagnoses ─┤                        │
  ├─> silver_transform_procedures ─┤                       │
  ├─> silver_transform_medications ─┤                      │
  ├─> silver_transform_lab_tests ─┤                        │
  ├─> silver_transform_claims ─┤                           │
  ├─> silver_transform_providers ─┤                        │
  └─> silver_transform_denials ─┘                          │
                              │                             │
                              ▼                             │
                    validate_silver_layer                   │
                              │                             │
                              ▼                             │
                        dbt_run_staging                     │
                              │                             │
                              ▼                             │
                        dbt_test_staging                    │
                              │                             │
                              ▼                             │
                        dbt_run_dimensions                  │
                              │                             │
                              ▼                             │
                        dbt_run_facts                       │
                              │                             │
                              ▼                             │
                        dbt_test_gold                       │
                              │                             │
                              ▼                             │
                    validate_gold_layer                     │
                              │                             │
                              ▼                             │
                    generate_quality_report                 │
                              │                             │
                              ▼                             │
                    refresh_superset_cache                  │
                              │                             │
                              ▼                             │
                            end                             │
```

## Data Models

### Entity Relationship Diagram

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│ dim_patient │◀────────│fact_encounter│────────▶│dim_provider │
└─────────────┘         └──────┬───────┘         └─────────────┘
                               │
                    ┌──────────┼──────────┐
                    │          │          │
                    ▼          ▼          ▼
            ┌──────────┐ ┌──────────┐ ┌──────────┐
            │fact_     │ │fact_lab_ │ │dim_      │
            │billing   │ │test      │ │diagnosis │
            └────┬─────┘ └──────────┘ └──────────┘
                 │
                 ▼
            ┌──────────┐
            │fact_     │
            │denial    │
            └──────────┘

All fact tables connect to dim_date via date_key foreign keys
```

### Key Metrics and Calculations

**Encounter Metrics**:
- Average length of stay by department
- Readmission rate by diagnosis
- Patient volume by provider and specialty

**Financial Metrics**:
- Claim denial rate: `COUNT(denied) / COUNT(total_claims)`
- Payment collection rate: `SUM(paid_amount) / SUM(billed_amount)`
- Average claim processing time: `AVG(payment_date - claim_date)`
- Revenue by department, provider, insurance type

**Clinical Metrics**:
- Most common diagnoses (ICD-10 codes)
- Procedure frequency and costs
- Medication prescribing patterns
- Lab test abnormality rates

## Error Handling

### Error Categories and Responses

| Error Type | Detection | Response | Recovery |
|------------|-----------|----------|----------|
| Missing CSV file | Bronze ingestion | Halt pipeline, alert | Manual file placement |
| Data quality failure | Great Expectations | Log details, continue with warning | Review and fix source |
| Schema mismatch | Silver transformation | Halt pipeline, alert | Update transformation code |
| Database connection | Gold load | Retry 3x, then alert | Check DB availability |
| dbt test failure | dbt test tasks | Halt pipeline, alert | Fix data or model |
| Referential integrity | Gold validation | Halt pipeline, alert | Fix transformation logic |

### Logging Strategy

**Log Levels**:
- **DEBUG**: Detailed execution steps, data samples
- **INFO**: Task start/completion, row counts, file paths
- **WARNING**: Data quality issues, missing optional fields
- **ERROR**: Task failures, exceptions, validation errors
- **CRITICAL**: Pipeline halt, data corruption detected

**Log Format** (JSON):
```json
{
  "timestamp": "2025-01-15T02:15:30Z",
  "level": "INFO",
  "dag_id": "healthcare_etl_pipeline",
  "task_id": "silver_transform_patients",
  "run_id": "scheduled__2025-01-15T02:00:00+00:00",
  "message": "Transformed 10,000 patient records",
  "metadata": {
    "input_rows": 10000,
    "output_rows": 9998,
    "duplicates_removed": 2,
    "execution_time_seconds": 12.5
  }
}
```

### Alerting Rules

**Critical Alerts** (immediate notification):
- Pipeline failure after all retries
- Data quality validation failure rate > 5%
- Database connection failure
- Missing required CSV files

**Warning Alerts** (daily digest):
- Individual data quality check failures
- Longer than expected execution time
- Unusual row count changes (>20% variance)

## Testing Strategy

### Unit Tests

**Python Functions**:
- Test date parsing and standardization
- Test missing data handling logic
- Test deduplication logic
- Test surrogate key generation
- Mock file I/O operations

**Framework**: pytest with fixtures

### Integration Tests

**End-to-End Pipeline**:
- Run pipeline with sample dataset (100 rows per table)
- Verify Bronze layer file creation
- Verify Silver layer Parquet files
- Verify Gold layer table row counts
- Verify star schema relationships

**Framework**: Airflow test mode with test database

### dbt Tests

**Generic Tests** (built-in):
- `unique`: Primary keys and surrogate keys
- `not_null`: Required fields
- `relationships`: Foreign key validity
- `accepted_values`: Enum fields

**Custom Tests**:
- Referential integrity across fact/dimension tables
- Date logic validation (start <= end)
- Aggregate consistency (sum of parts = total)
- No orphaned records in fact tables

### Data Quality Tests

**Great Expectations Suites**:
- Schema validation (column names, types, order)
- Statistical validation (mean, std dev, percentiles)
- Pattern matching (regex for IDs, emails, phones)
- Cross-table validation (row count consistency)

### Performance Tests

**Benchmarks**:
- Bronze ingestion: < 30 seconds for all files
- Silver transformation: < 2 minutes per table
- dbt Gold layer: < 5 minutes total
- End-to-end pipeline: < 15 minutes

**Monitoring**:
- Track execution time trends
- Alert on >50% increase in processing time
- Monitor database query performance

## Configuration Management

### Environment Variables

```bash
# Database connections
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=healthcare_warehouse
POSTGRES_USER=etl_user
POSTGRES_PASSWORD=<secret>

# File paths
BRONZE_DATA_PATH=/data/bronze
SILVER_DATA_PATH=/data/silver
SOURCE_CSV_PATH=/data/source

# Airflow
AIRFLOW__CORE__DAGS_FOLDER=/opt/airflow/dags
AIRFLOW__CORE__LOAD_EXAMPLES=False

# Alerts
ALERT_EMAIL=data-team@hospital.com
SLACK_WEBHOOK_URL=<webhook>
```

### Configuration Files

**config/pipeline_config.yaml**:
```yaml
pipeline:
  name: healthcare_etl
  version: 1.0.0
  
bronze:
  source_path: ${SOURCE_CSV_PATH}
  target_path: ${BRONZE_DATA_PATH}
  tables:
    - patients
    - encounters
    - diagnoses
    - procedures
    - medications
    - lab_tests
    - claims_and_billing
    - providers
    - denials

silver:
  source_path: ${BRONZE_DATA_PATH}
  target_path: ${SILVER_DATA_PATH}
  date_format: "%d-%m-%Y"
  target_date_format: "%Y-%m-%d"
  
data_quality:
  fail_on_error: true
  warning_threshold: 0.05  # 5% failure rate
  
gold:
  database: ${POSTGRES_DB}
  schema: public
  incremental_strategy: merge
```

## Deployment Strategy

### Local Development

1. Docker Compose setup with:
   - Airflow (webserver, scheduler, worker)
   - PostgreSQL database
   - Great Expectations
   - Superset

2. Volume mounts for:
   - DAGs directory
   - Data directories (Bronze/Silver)
   - dbt project
   - Configuration files

### Production Deployment

1. **Infrastructure**:
   - Managed Airflow (e.g., Cloud Composer, MWAA, or self-hosted)
   - Managed PostgreSQL (RDS, Cloud SQL)
   - Object storage for Bronze/Silver (S3, GCS) - optional upgrade

2. **CI/CD Pipeline**:
   - Run pytest unit tests
   - Run dbt tests on sample data
   - Deploy DAGs to Airflow
   - Deploy dbt models
   - Update Great Expectations suites

3. **Monitoring**:
   - Airflow UI for DAG monitoring
   - PostgreSQL query performance monitoring
   - Data quality dashboard in Superset
   - Log aggregation (ELK stack or similar)

## Visualization Design

### Apache Superset Dashboards

**Dashboard 1: Operational Overview**
- KPI cards: Total patients, encounters, providers
- Line chart: Daily admission trends by visit type
- Bar chart: Top 10 departments by patient volume
- Pie chart: Visit type distribution
- Table: Recent encounters with status

**Dashboard 2: Financial Analytics**
- KPI cards: Total billed, total paid, collection rate, denial rate
- Line chart: Daily revenue and payment trends
- Bar chart: Revenue by insurance provider
- Funnel chart: Claim status breakdown
- Table: Top denial reasons with counts and amounts

**Dashboard 3: Clinical Insights**
- Bar chart: Top 20 diagnoses by frequency
- Bar chart: Top 20 procedures by volume
- Heatmap: Readmission rates by department and diagnosis
- Table: Chronic condition patients with encounter counts

**Dashboard 4: Provider Performance**
- Bar chart: Patient volume by provider
- Scatter plot: Provider experience vs. patient volume
- Table: Provider utilization with specialty and department
- Bar chart: Average length of stay by provider

**Dashboard 5: Medication Analysis**
- Bar chart: Top 20 medications by prescription count
- Line chart: Medication cost trends over time
- Bar chart: Prescriptions by prescriber
- Table: High-cost medications with average cost

### Dashboard Refresh Strategy

- Automatic refresh after successful pipeline completion
- Manual refresh button for ad-hoc analysis
- Cache TTL: 1 hour for query results
- Pre-cache common queries during off-peak hours

## Future Enhancements

**Phase 2 Considerations** (not in current scope):
- Apache Kafka for real-time streaming ingestion
- PySpark for processing larger datasets (>10M rows)
- BigQuery as cloud data warehouse
- MLflow for predictive models (readmission risk, cost prediction)
- CDC (Change Data Capture) for incremental Bronze ingestion
- Data lineage tracking with OpenLineage
- Advanced anomaly detection in data quality checks
