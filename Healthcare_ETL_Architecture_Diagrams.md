# Healthcare ETL Pipeline - Architecture Diagrams

## Diagram 1: High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           Healthcare ETL Pipeline                                │
│                         Docker Compose Environment                               │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │    │   Orchestration │    │   Data Storage  │    │   Analytics     │
│                 │    │                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ CSV Files   │ │───▶│ │   Airflow   │ │───▶│ │ PostgreSQL  │ │───▶│ │  Superset   │ │
│ │ (9 tables)  │ │    │ │ Scheduler   │ │    │ │ Warehouse   │ │    │ │ Dashboards  │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│                 │    │                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ Validation  │ │    │ │   Airflow   │ │    │ │   Bronze    │ │    │ │   Reports   │ │
│ │ Rules       │ │    │ │   WebUI     │ │    │ │   Layer     │ │    │ │ & Alerts    │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
        │                        │                        │                        │
        │                        │                        │                        │
        ▼                        ▼                        ▼                        ▼
   Port: Files              Port: 8080              Port: 5433              Port: 8088
```

## Diagram 2: Medallion Architecture Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          Medallion Architecture                                  │
│                     Bronze → Silver → Gold Layers                               │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   BRONZE LAYER  │    │  SILVER LAYER   │    │   GOLD LAYER    │    │   ANALYTICS     │
│   (Raw Data)    │    │ (Cleaned Data)  │    │ (Business Data) │    │   (Insights)    │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│                 │    │                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ patients.csv│ │───▶│ │patients.pqt │ │───▶│ │ dim_patient │ │───▶│ │Patient Flow │ │
│ │encounters.csv│ │───▶│ │encounters.pqt│ │───▶│ │fact_encounter│ │───▶│ │Operational  │ │
│ │diagnoses.csv│ │───▶│ │diagnoses.pqt│ │───▶│ │dim_diagnosis│ │───▶│ │Dashboard    │ │
│ │procedures.csv│ │───▶│ │procedures.pqt│ │───▶│ │dim_procedure│ │───▶│ └─────────────┘ │
│ │medications.csv│ │───▶│ │medications.pqt│ │───▶│ │dim_medication│ │───▶│ ┌─────────────┐ │
│ │lab_tests.csv│ │───▶│ │lab_tests.pqt│ │───▶│ │fact_lab_test│ │───▶│ │Financial    │ │
│ │claims.csv   │ │───▶│ │claims.pqt   │ │───▶│ │fact_billing │ │───▶│ │Analytics    │ │
│ │providers.csv│ │───▶│ │providers.pqt│ │───▶│ │dim_provider │ │───▶│ │Dashboard    │ │
│ │denials.csv  │ │───▶│ │denials.pqt  │ │───▶│ │fact_denial  │ │───▶│ └─────────────┘ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │    │ ┌─────────────┐ │
│                 │    │                 │    │                 │    │ │Clinical     │ │
│ Format: CSV     │    │ Format: Parquet │    │ Format: Tables  │    │ │Quality      │ │
│ Storage: Files  │    │ Storage: Files  │    │ Storage: Postgres│    │ │Dashboard    │ │
│ Validation:     │    │ Validation:     │    │ Validation:     │    │ └─────────────┘ │
│ - File exists   │    │ - Great Expect. │    │ - dbt tests     │    │                 │
│ - Row counts    │    │ - Schema valid. │    │ - Referential   │    │                 │
│ - Checksums     │    │ - Business rules│    │ - Integrity     │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Diagram 3: Airflow DAG Workflow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        Airflow DAG: healthcare_etl_pipeline                      │
│                           Schedule: Daily at 2:00 AM UTC                         │
└─────────────────────────────────────────────────────────────────────────────────┘

                                    ┌─────────────┐
                                    │    START    │
                                    └──────┬──────┘
                                           │
                                    ┌──────▼──────┐
                                    │ Validate    │
                                    │ Source Files│
                                    └──────┬──────┘
                                           │
                                    ┌──────▼──────┐
                                    │ Ingest      │
                                    │ Bronze Layer│
                                    └──────┬──────┘
                                           │
                                    ┌──────▼──────┐
                                    │ Validate    │
                                    │ Bronze Layer│
                                    └──────┬──────┘
                                           │
                    ┌──────────────────────▼──────────────────────┐
                    │           Silver Transformations            │
                    │              (Parallel Tasks)               │
                    ├─────────┬─────────┬─────────┬─────────┬─────┤
                    │Transform│Transform│Transform│Transform│ ... │
                    │patients │encounters│diagnoses│procedures│     │
                    └─────────┴─────────┴─────────┴─────────┴─────┘
                                           │
                                    ┌──────▼──────┐
                                    │ Validate    │
                                    │ Silver Layer│
                                    │(Great Expect)│
                                    └──────┬──────┘
                                           │
                                    ┌──────▼──────┐
                                    │ Load to     │
                                    │ Warehouse   │
                                    └──────┬──────┘
                                           │
                    ┌──────────────────────▼──────────────────────┐
                    │              dbt Gold Layer                 │
                    │             (Sequential Tasks)              │
                    ├──────┬──────┬──────┬──────┬──────┬─────────┤
                    │ dbt  │ dbt  │ dbt  │ dbt  │ dbt  │  dbt    │
                    │ deps │ stg  │ test │ dims │ facts│ test    │
                    └──────┴──────┴──────┴──────┴──────┴─────────┘
                                           │
                                    ┌──────▼──────┐
                                    │ Validate    │
                                    │ Gold Layer  │
                                    └──────┬──────┘
                                           │
                                    ┌──────▼──────┐
                                    │ Generate    │
                                    │ DQ Report   │
                                    └──────┬──────┘
                                           │
                                    ┌──────▼──────┐
                                    │ Refresh     │
                                    │ Superset    │
                                    └──────┬──────┘
                                           │
                                    ┌──────▼──────┐
                                    │     END     │
                                    └─────────────┘

Retry Policy: 3 attempts with exponential backoff
Timeout: 2 hours maximum
Alerts: Email on failure, optional on success
```

## Diagram 4: Data Quality Framework

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          Data Quality Framework                                  │
│                        Great Expectations Integration                            │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  BRONZE LAYER   │    │  SILVER LAYER   │    │   GOLD LAYER    │    │   REPORTING     │
│   Validation    │    │   Validation    │    │   Validation    │    │   & Alerts      │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│                 │    │                 │    │                 │    │                 │
│ ✓ File Exists   │    │ ✓ Schema Valid  │    │ ✓ Row Counts    │    │ ┌─────────────┐ │
│ ✓ Row Counts    │    │ ✓ Data Types    │    │ ✓ Referential   │    │ │ JSON Report │ │
│ ✓ File Size     │    │ ✓ Primary Keys  │    │   Integrity     │    │ │ - Success % │ │
│ ✓ Checksums     │    │ ✓ Value Ranges  │    │ ✓ Business Rules│    │ │ - Failed    │ │
│                 │    │ ✓ Date Logic    │    │ ✓ Aggregations  │    │ │   Tests     │ │
│ Checkpoint:     │    │ ✓ Patterns      │    │                 │    │ │ - Metrics   │ │
│ bronze_validate │    │ ✓ Uniqueness    │    │ Tool: dbt tests │    │ └─────────────┘ │
│                 │    │ ✓ Completeness  │    │                 │    │                 │
│ Tool: Python    │    │                 │    │ Checkpoint:     │    │ ┌─────────────┐ │
│ Custom Logic    │    │ Checkpoint:     │    │ gold_validate   │    │ │ Email Alert │ │
│                 │    │ silver_validate │    │ (Future)        │    │ │ - Failures  │ │
│ Failure Action: │    │                 │    │                 │    │ │ - Summary   │ │
│ ❌ Stop Pipeline │    │ Failure Action: │    │ Failure Action: │    │ │ - Logs      │ │
│                 │    │ ⚠️  Continue    │    │ ❌ Stop Pipeline │    │ └─────────────┘ │
│                 │    │   with Warning  │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │                        │
         ▼                        ▼                        ▼                        ▼
   Threshold:                Threshold:                Threshold:                Dashboard:
   0% failures              5% failures              0% failures              Superset
```

## Diagram 5: Database Schema (Gold Layer)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            Star Schema Design                                   │
│                          PostgreSQL Warehouse                                   │
└─────────────────────────────────────────────────────────────────────────────────┘

                              DIMENSION TABLES
    ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
    │   dim_patient   │  │  dim_provider   │  │ dim_diagnosis   │  │ dim_procedure   │
    ├─────────────────┤  ├─────────────────┤  ├─────────────────┤  ├─────────────────┤
    │ patient_key (PK)│  │provider_key (PK)│  │diagnosis_key(PK)│  │procedure_key(PK)│
    │ patient_id      │  │ provider_id     │  │ diagnosis_code  │  │ procedure_code  │
    │ first_name      │  │ first_name      │  │ description     │  │ description     │
    │ last_name       │  │ last_name       │  │ category        │  │ category        │
    │ dob             │  │ specialty       │  │ severity        │  │ body_system     │
    │ gender          │  │ department      │  │ chronic_flag    │  │ complexity      │
    │ ethnicity       │  │ license_number  │  │ effective_date  │  │ effective_date  │
    │ insurance_type  │  │ hire_date       │  │ expiry_date     │  │ expiry_date     │
    │ effective_date  │  │ effective_date  │  │ is_current      │  │ is_current      │
    │ expiry_date     │  │ expiry_date     │  │ created_at      │  │ created_at      │
    │ is_current      │  │ is_current      │  │ updated_at      │  │ updated_at      │
    │ created_at      │  │ created_at      │  │                 │  │                 │
    │ updated_at      │  │ updated_at      │  │                 │  │                 │
    └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘
             │                     │                     │                     │
             │                     │                     │                     │
             └─────────────────────┼─────────────────────┼─────────────────────┘
                                   │                     │
                                   ▼                     ▼
                            ┌─────────────────┐  ┌─────────────────┐
                            │ dim_medication  │  │   dim_date      │
                            ├─────────────────┤  ├─────────────────┤
                            │medication_key(PK)│  │ date_key (PK)   │
                            │ medication_name │  │ full_date       │
                            │ generic_name    │  │ year            │
                            │ brand_name      │  │ quarter         │
                            │ drug_class      │  │ month           │
                            │ dosage_form     │  │ week            │
                            │ strength        │  │ day_of_week     │
                            │ route           │  │ day_of_month    │
                            │ manufacturer    │  │ day_of_year     │
                            │ ndc_code        │  │ is_weekend      │
                            │ effective_date  │  │ is_holiday      │
                            │ expiry_date     │  │ fiscal_year     │
                            │ is_current      │  │ fiscal_quarter  │
                            │ created_at      │  │                 │
                            │ updated_at      │  │                 │
                            └─────────────────┘  └─────────────────┘
                                     │                     │
                                     └─────────┬───────────┘
                                               │
                                               ▼
                                    FACT TABLES
    ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
    │ fact_encounter  │  │  fact_billing   │  │ fact_lab_test   │  │  fact_denial    │
    ├─────────────────┤  ├─────────────────┤  ├─────────────────┤  ├─────────────────┤
    │encounter_key(PK)│  │ billing_key(PK) │  │lab_test_key(PK) │  │ denial_key (PK) │
    │ encounter_id    │  │ claim_id        │  │ test_id         │  │ denial_id       │
    │ patient_key (FK)│  │ encounter_key(FK)│  │encounter_key(FK)│  │ claim_key (FK)  │
    │ provider_key(FK)│  │ patient_key (FK)│  │ patient_key (FK)│  │ patient_key(FK) │
    │ admission_date  │  │ provider_key(FK)│  │ provider_key(FK)│  │ provider_key(FK)│
    │ discharge_date  │  │ service_date    │  │ test_date       │  │ denial_date     │
    │ encounter_type  │  │ charge_amount   │  │ test_name       │  │ denial_reason   │
    │ department      │  │ payment_amount  │  │ result_value    │  │ denial_category │
    │ length_of_stay  │  │ insurance_paid  │  │ reference_range │  │ appeal_status   │
    │ discharge_status│  │ patient_paid    │  │ abnormal_flag   │  │ resolution_date │
    │ primary_diag_key│  │ adjustment_amt  │  │ critical_flag   │  │ recovered_amount│
    │ total_charges   │  │ outstanding_amt │  │ units           │  │ write_off_amount│
    │ created_at      │  │ billing_status  │  │ lab_department  │  │ created_at      │
    │ updated_at      │  │ created_at      │  │ created_at      │  │ updated_at      │
    └─────────────────┘  │ updated_at      │  │ updated_at      │  └─────────────────┘
                         └─────────────────┘  └─────────────────┘

Key Features:
- Surrogate Keys (patient_key, provider_key, etc.)
- Slowly Changing Dimensions (SCD Type 2)
- Audit Columns (created_at, updated_at)
- Foreign Key Relationships
- Optimized for Analytics Queries
```

## Diagram 6: Docker Container Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          Docker Compose Architecture                            │
│                            healthcare-etl-network                               │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                                HOST MACHINE                                     │
│                              (macOS/Linux/Windows)                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   AIRFLOW       │  │   DATABASES     │  │   ANALYTICS     │  │   VOLUMES   │ │
│  │   SERVICES      │  │                 │  │                 │  │             │ │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────────┤  ├─────────────┤ │
│  │                 │  │                 │  │                 │  │             │ │
│  │┌───────────────┐│  │┌───────────────┐│  │┌───────────────┐│  │┌───────────┐│ │
│  ││airflow-       ││  ││   postgres    ││  ││   superset    ││  ││postgres-  ││ │
│  ││webserver      ││  ││  (metadata)   ││  ││  (analytics)  ││  ││db-volume  ││ │
│  ││               ││  ││               ││  ││               ││  ││           ││ │
│  ││Port: 8080     ││  ││Port: 5432     ││  ││Port: 8088     ││  ││Persistent ││ │
│  ││Image: Custom  ││  ││Image: postgres││  ││Image: superset││  ││Storage    ││ │
│  │└───────────────┘│  │└───────────────┘│  │└───────────────┘│  │└───────────┘│ │
│  │                 │  │                 │  │                 │  │             │ │
│  │┌───────────────┐│  │┌───────────────┐│  │                 │  │┌───────────┐│ │
│  ││airflow-       ││  ││ warehouse-db  ││  │                 │  ││warehouse- ││ │
│  ││scheduler      ││  ││  (data)       ││  │                 │  ││db-volume  ││ │
│  ││               ││  ││               ││  │                 │  ││           ││ │
│  ││Background     ││  ││Port: 5433     ││  │                 │  ││Persistent ││ │
│  ││Image: Custom  ││  ││Image: postgres││  │                 │  ││Storage    ││ │
│  │└───────────────┘│  │└───────────────┘│  │                 │  │└───────────┘│ │
│  │                 │  │                 │  │                 │  │             │ │
│  │┌───────────────┐│  │                 │  │                 │  │┌───────────┐│ │
│  ││airflow-init   ││  │                 │  │                 │  ││superset-  ││ │
│  ││(one-time)     ││  │                 │  │                 │  ││volume     ││ │
│  ││               ││  │                 │  │                 │  ││           ││ │
│  ││Setup Only     ││  │                 │  │                 │  ││Persistent ││ │
│  ││Image: Custom  ││  │                 │  │                 │  ││Storage    ││ │
│  │└───────────────┘│  │                 │  │                 │  │└───────────┘│ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────┘ │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                            SHARED VOLUMES                                   │ │
│  ├─────────────────────────────────────────────────────────────────────────────┤ │
│  │ ./airflow/dags     → /opt/airflow/dags        (DAG definitions)            │ │
│  │ ./airflow/logs     → /opt/airflow/logs        (Execution logs)             │ │
│  │ ./data/bronze      → /opt/airflow/data/bronze (Raw CSV files)              │ │
│  │ ./data/silver      → /opt/airflow/data/silver (Parquet files)              │ │
│  │ ./dataset          → /opt/airflow/dataset     (Source CSV files)           │ │
│  │ ./config           → /opt/airflow/config      (Configuration files)        │ │
│  │ ./dbt_project      → /opt/airflow/dbt_project (dbt models)                 │ │
│  │ ./great_expectations → /opt/airflow/great_expectations (Data quality)      │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                          NETWORK CONFIGURATION                              │ │
│  ├─────────────────────────────────────────────────────────────────────────────┤ │
│  │ Network: healthcare-etl-network (bridge)                                   │ │
│  │ Internal DNS: Service names resolve to containers                           │ │
│  │ External Access: Host ports mapped to container ports                       │ │
│  │                                                                             │ │
│  │ Service Communication:                                                      │ │
│  │ - airflow-webserver → postgres (metadata)                                  │ │
│  │ - airflow-scheduler → postgres (metadata)                                  │ │
│  │ - airflow-webserver → warehouse-db (ETL data)                              │ │
│  │ - superset → warehouse-db (analytics data)                                 │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘

Health Checks:
✓ postgres: pg_isready -U airflow
✓ warehouse-db: pg_isready -U etl_user -d healthcare_warehouse  
✓ airflow-webserver: curl http://localhost:8080/health
✓ superset: curl http://localhost:8088/health

Resource Requirements:
- Memory: 4GB minimum, 8GB recommended
- Storage: 10GB for data and logs
- CPU: 2+ cores for parallel processing
```

## Diagram 7: Data Quality Validation Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        Data Quality Validation Pipeline                         │
│                         Great Expectations Framework                            │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   DATA INPUT    │    │   VALIDATION    │    │   RESULTS       │    │   ACTIONS       │
│                 │    │   CHECKPOINTS   │    │   PROCESSING    │    │                 │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│                 │    │                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ Bronze CSV  │ │───▶│ │ File Checks │ │───▶│ │ Validation  │ │───▶│ │ Continue    │ │
│ │ Files       │ │    │ │ - Exists    │ │    │ │ Results     │ │    │ │ Pipeline    │ │
│ │             │ │    │ │ - Size > 0  │ │    │ │ - Pass/Fail │ │    │ │ (Success)   │ │
│ └─────────────┘ │    │ │ - Row Count │ │    │ │ - Metrics   │ │    │ └─────────────┘ │
│                 │    │ └─────────────┘ │    │ │ - Details   │ │    │                 │
│ ┌─────────────┐ │    │                 │    │ └─────────────┘ │    │ ┌─────────────┐ │
│ │ Silver      │ │───▶│ ┌─────────────┐ │───▶│                 │───▶│ │ Stop        │ │
│ │ Parquet     │ │    │ │ Schema      │ │    │ ┌─────────────┐ │    │ │ Pipeline    │ │
│ │ Files       │ │    │ │ Validation  │ │    │ │ Statistics  │ │    │ │ (Failure)   │ │
│ │             │ │    │ │ - Columns   │ │    │ │ - Success % │ │    │ └─────────────┘ │
│ └─────────────┘ │    │ │ - Types     │ │    │ │ - Failed    │ │    │                 │
│                 │    │ │ - Not Null  │ │    │ │   Count     │ │    │ ┌─────────────┐ │
│ ┌─────────────┐ │    │ └─────────────┘ │    │ │ - Error     │ │    │ │ Send        │ │
│ │ Gold        │ │───▶│                 │    │ │   Details   │ │    │ │ Alerts      │ │
│ │ Tables      │ │    │ ┌─────────────┐ │    │ └─────────────┘ │    │ │ - Email     │ │
│ │             │ │    │ │ Business    │ │    │                 │    │ │ - Slack     │ │
│ └─────────────┘ │    │ │ Rules       │ │    │ ┌─────────────┐ │    │ │ - Dashboard │ │
│                 │    │ │ - Age Range │ │    │ │ JSON Report │ │    │ └─────────────┘ │
│                 │    │ │ - Date Logic│ │    │ │ - Timestamp │ │    │                 │
│                 │    │ │ - Patterns  │ │    │ │ - Run Info  │ │    │ ┌─────────────┐ │
│                 │    │ │ - Referential│ │    │ │ - All Tests │ │    │ │ Generate    │ │
│                 │    │ │   Integrity │ │    │ │ - Metrics   │ │    │ │ Reports     │ │
│                 │    │ └─────────────┘ │    │ └─────────────┘ │    │ │ - HTML      │ │
│                 │    │                 │    │                 │    │ │ - JSON      │ │
└─────────────────┘    └─────────────────┘    └─────────────────┘    │ │ - Dashboard │ │
                                                                      │ └─────────────┘ │
                                                                      └─────────────────┘

Validation Rules Examples:

┌─────────────────────────────────────────────────────────────────────────────────┐
│                              EXPECTATION SUITE                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│ Schema Expectations:                                                            │
│ ✓ expect_table_columns_to_match_ordered_list                                    │
│ ✓ expect_column_values_to_not_be_null (patient_id, encounter_id)               │
│ ✓ expect_column_values_to_be_of_type (age: int, admission_date: date)          │
│                                                                                 │
│ Business Rule Expectations:                                                     │
│ ✓ expect_column_values_to_be_between (age: 0-120, length_of_stay: 0-365)      │
│ ✓ expect_column_values_to_match_regex (patient_id: "^PAT[0-9]{5}$")            │
│ ✓ expect_column_pair_values_A_to_be_greater_than_B (discharge_date > admission) │
│                                                                                 │
│ Data Quality Expectations:                                                      │
│ ✓ expect_column_values_to_be_unique (patient_id, encounter_id)                 │
│ ✓ expect_column_values_to_be_in_set (gender: ['M', 'F', 'Other'])             │
│ ✓ expect_table_row_count_to_be_between (min: 1, max: 1000000)                 │
│                                                                                 │
│ Referential Integrity:                                                         │
│ ✓ expect_column_values_to_be_in_type_list (foreign keys exist in parent)      │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

Configuration:
- Threshold: 5% failure rate allowed
- Action on Failure: Continue with warning (Silver), Stop pipeline (Bronze/Gold)
- Reporting: JSON files + Email alerts + Superset dashboard
```

## Diagram 8: Monitoring & Alerting Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        Monitoring & Alerting System                             │
│                      Multi-Channel Notification System                          │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   DATA SOURCES  │    │   MONITORING    │    │   PROCESSING    │    │   ALERTING      │
│                 │    │   COLLECTION    │    │   & ANALYSIS    │    │   CHANNELS      │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│                 │    │                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ Airflow     │ │───▶│ │ Task Status │ │───▶│ │ Alert Rules │ │───▶│ │ Email       │ │
│ │ Task Logs   │ │    │ │ - Success   │ │    │ │ - Critical  │ │    │ │ Notifications│ │
│ │ - Execution │ │    │ │ - Failed    │ │    │ │ - Warning   │ │    │ │ - Failures  │ │
│ │ - Duration  │ │    │ │ - Running   │ │    │ │ - Info      │ │    │ │ - Summary   │ │
│ │ - Retries   │ │    │ │ - Retry     │ │    │ └─────────────┘ │    │ │ - Logs      │ │
│ └─────────────┘ │    │ └─────────────┘ │    │                 │    │ └─────────────┘ │
│                 │    │                 │    │ ┌─────────────┐ │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ │ Threshold   │ │    │ ┌─────────────┐ │
│ │ Data        │ │───▶│ │ Quality     │ │───▶│ │ Monitoring  │ │───▶│ │ Slack       │ │
│ │ Quality     │ │    │ │ Metrics     │ │    │ │ - Success % │ │    │ │ Webhooks    │ │
│ │ Results     │ │    │ │ - Pass Rate │ │    │ │ - Row Count │ │    │ │ - Real-time │ │
│ │ - GE Reports│ │    │ │ - Failed    │ │    │ │ - Duration  │ │    │ │ - Channels  │ │
│ │ - dbt Tests │ │    │ │   Tests     │ │    │ │ - Error Rate│ │    │ │ - @mentions │ │
│ └─────────────┘ │    │ │ - Row Counts│ │    │ └─────────────┘ │    │ └─────────────┘ │
│                 │    │ └─────────────┘ │    │                 │    │                 │
│ ┌─────────────┐ │    │                 │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ System      │ │───▶│ ┌─────────────┐ │───▶│ │ Alert       │ │───▶│ │ Dashboard   │ │
│ │ Metrics     │ │    │ │ Performance │ │    │ │ Aggregation │ │    │ │ Monitoring  │ │
│ │ - CPU Usage │ │    │ │ Metrics     │ │    │ │ - Dedup     │ │    │ │ - Superset  │ │
│ │ - Memory    │ │    │ │ - Exec Time │ │    │ │ - Priority  │ │    │ │ - Grafana   │ │
│ │ - Disk I/O  │ │    │ │ - Throughput│ │    │ │ - Batching  │ │    │ │ - Custom    │ │
│ │ - Network   │ │    │ │ - Latency   │ │    │ │ - Routing   │ │    │ │   Views     │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│                 │    │                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ Database    │ │───▶│ │ Connection  │ │───▶│ │ Escalation  │ │───▶│ │ PagerDuty   │ │
│ │ Health      │ │    │ │ Monitoring  │ │    │ │ Rules       │ │    │ │ Integration │ │
│ │ - Postgres  │ │    │ │ - Uptime    │ │    │ │ - Severity  │ │    │ │ - On-call   │ │
│ │ - Superset  │ │    │ │ - Response  │ │    │ │ - Repeat    │ │    │ │ - Incidents │ │
│ │ - Airflow   │ │    │ │ - Errors    │ │    │ │ - Timeout   │ │    │ │ - Escalation│ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘

Alert Severity Levels:

┌─────────────────────────────────────────────────────────────────────────────────┐
│                              ALERT CLASSIFICATION                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│ 🔴 CRITICAL (Immediate Action Required):                                        │
│    - Pipeline complete failure                                                  │
│    - Database connection lost                                                   │
│    - Data corruption detected                                                   │
│    - Security breach indicators                                                 │
│    → Action: Page on-call engineer, stop pipeline                              │
│                                                                                 │
│ 🟡 WARNING (Attention Needed):                                                  │
│    - Data quality threshold exceeded (>5% failures)                            │
│    - Performance degradation (>50% slower)                                     │
│    - Retry attempts exhausted                                                   │
│    - Disk space running low                                                     │
│    → Action: Email team, continue with monitoring                              │
│                                                                                 │
│ 🟢 INFO (Informational):                                                        │
│    - Pipeline completed successfully                                            │
│    - Data quality validation passed                                             │
│    - Scheduled maintenance completed                                            │
│    - Performance benchmarks met                                                 │
│    → Action: Log event, optional notification                                  │
│                                                                                 │
│ 📊 METRICS (Trending Data):                                                     │
│    - Daily processing volumes                                                   │
│    - Quality score trends                                                       │
│    - Performance metrics                                                        │
│    - Resource utilization                                                       │
│    → Action: Dashboard updates, weekly reports                                 │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

Notification Templates:
- Email: HTML with logs, metrics, and action items
- Slack: Formatted messages with thread replies
- Dashboard: Real-time status indicators
- Reports: Weekly/monthly trend analysis
```

These diagrams provide a comprehensive visual representation of your Healthcare ETL Pipeline project, covering:

1. **High-Level System Architecture** - Overall system components and their relationships
2. **Medallion Architecture Data Flow** - Bronze → Silver → Gold transformation process
3. **Airflow DAG Workflow** - Detailed task dependencies and execution flow
4. **Data Quality Framework** - Great Expectations validation process
5. **Database Schema Design** - Star schema with fact and dimension tables
6. **Docker Container Architecture** - Infrastructure and deployment setup
7. **Data Quality Validation Flow** - Comprehensive quality assurance process
8. **Monitoring & Alerting Architecture** - Multi-channel notification system

Each diagram includes detailed annotations and explanations to help stakeholders understand the technical architecture and data flow of your healthcare ETL pipeline.