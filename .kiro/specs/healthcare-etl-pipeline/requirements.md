# Requirements Document

## Introduction

This document specifies the requirements for an automated ETL (Extract, Transform, Load) pipeline for a California-based hospital's Q1 2025 operational data. The system will orchestrate data ingestion from CSV files, perform multi-layer transformations following the medallion architecture (Bronze/Silver/Gold), implement data quality checks, and enable analytics through a star schema warehouse with visualization capabilities.

## Glossary

- **ETL System**: The complete Extract, Transform, Load pipeline orchestrated by Apache Airflow
- **Bronze Layer**: Raw, immutable CSV data storage representing the source of truth
- **Silver Layer**: Cleaned and validated data stored in Parquet format with applied transformations
- **Gold Layer**: Business-ready star schema warehouse with dimension and fact tables
- **Airflow DAG**: Directed Acyclic Graph defining the workflow orchestration in Apache Airflow
- **Data Quality Engine**: Great Expectations framework for validating data integrity
- **Analytics Warehouse**: PostgreSQL database storing the final star schema
- **Visualization Layer**: Apache Superset dashboard for analytical insights
- **dbt Models**: Data Build Tool transformations for modeling and testing warehouse data

## Requirements

### Requirement 1

**User Story:** As a data engineer, I want the ETL System to automatically extract raw hospital data from CSV files, so that I can maintain an immutable source of truth in the Bronze Layer

#### Acceptance Criteria

1. WHEN the Airflow DAG executes, THE ETL System SHALL read all 9 CSV files from the dataset directory (patients, encounters, diagnoses, procedures, medications, lab_tests, claims_and_billing, providers, denials)
2. THE ETL System SHALL store raw CSV data in the Bronze Layer without any modifications to preserve data lineage
3. THE ETL System SHALL validate that all expected CSV files are present before proceeding to transformation
4. THE ETL System SHALL log the row count and file size for each ingested CSV file
5. IF any CSV file is missing or corrupted, THEN THE ETL System SHALL raise an alert and halt the pipeline execution

### Requirement 2

**User Story:** As a data engineer, I want the ETL System to clean and transform raw data into the Silver Layer, so that downstream analytics can work with high-quality standardized data

#### Acceptance Criteria

1. THE ETL System SHALL transform Bronze Layer CSV files into Parquet format in the Silver Layer
2. THE ETL System SHALL handle missing data by applying appropriate imputation or null handling strategies
3. THE ETL System SHALL standardize date formats across all tables to ISO 8601 format (YYYY-MM-DD)
4. THE ETL System SHALL remove duplicate records based on primary key fields
5. THE ETL System SHALL validate data types and convert fields to appropriate types (integers, floats, dates, strings)
6. THE ETL System SHALL create audit columns (load_timestamp, source_file) for each Silver Layer record

### Requirement 3

**User Story:** As a data analyst, I want the ETL System to create a star schema in the Gold Layer, so that I can perform efficient analytical queries on hospital operations

#### Acceptance Criteria

1. THE ETL System SHALL create dimension tables (dim_patient, dim_provider, dim_date, dim_diagnosis, dim_procedure, dim_medication) in the Analytics Warehouse
2. THE ETL System SHALL create fact tables (fact_encounter, fact_billing, fact_lab_test, fact_denial) with foreign keys to dimension tables
3. THE ETL System SHALL implement slowly changing dimension (SCD) Type 2 for dim_patient to track historical changes
4. THE ETL System SHALL denormalize frequently joined attributes into fact tables to optimize query performance
5. THE ETL System SHALL create surrogate keys for all dimension tables
6. THE ETL System SHALL maintain referential integrity between fact and dimension tables

### Requirement 4

**User Story:** As a data quality manager, I want the Data Quality Engine to validate data at each pipeline stage, so that I can ensure data accuracy and completeness before it reaches analysts

#### Acceptance Criteria

1. THE Data Quality Engine SHALL validate that patient_id, encounter_id, and provider_id follow expected format patterns
2. THE Data Quality Engine SHALL check that numeric fields (costs, amounts) are within reasonable ranges
3. THE Data Quality Engine SHALL verify that date fields contain valid dates and follow logical sequences (admission_date <= discharge_date)
4. THE Data Quality Engine SHALL ensure referential integrity between related tables (encounters reference valid patients)
5. IF data quality checks fail, THEN THE ETL System SHALL log detailed failure information and send notifications
6. THE Data Quality Engine SHALL generate data quality reports after each pipeline run

### Requirement 5

**User Story:** As a DevOps engineer, I want the Airflow DAG to orchestrate the entire pipeline with proper scheduling and monitoring, so that the ETL process runs reliably without manual intervention

#### Acceptance Criteria

1. THE Airflow DAG SHALL execute the complete ETL pipeline on a daily schedule at 2:00 AM UTC
2. THE Airflow DAG SHALL implement task dependencies ensuring Bronze completes before Silver, and Silver before Gold
3. THE Airflow DAG SHALL retry failed tasks up to 3 times with exponential backoff
4. THE Airflow DAG SHALL send email notifications on pipeline failure or success
5. THE Airflow DAG SHALL implement task timeout limits to prevent hung processes
6. THE Airflow DAG SHALL expose metrics (execution time, row counts, data quality scores) for monitoring

### Requirement 6

**User Story:** As a data analyst, I want dbt models to transform Silver Layer data into Gold Layer analytics tables, so that business logic is version-controlled and testable

#### Acceptance Criteria

1. THE dbt Models SHALL define transformations for creating all dimension and fact tables
2. THE dbt Models SHALL include data tests for uniqueness, not-null constraints, and referential integrity
3. THE dbt Models SHALL generate documentation describing each model, column, and transformation logic
4. THE dbt Models SHALL implement incremental loading for fact tables to optimize processing time
5. WHEN dbt tests fail, THEN THE ETL System SHALL prevent promotion of data to the Gold Layer

### Requirement 7

**User Story:** As a hospital administrator, I want the Visualization Layer to provide interactive dashboards, so that I can monitor key operational and financial metrics

#### Acceptance Criteria

1. THE Visualization Layer SHALL display patient admission trends by department and visit type
2. THE Visualization Layer SHALL show claim denial rates with breakdown by denial reason
3. THE Visualization Layer SHALL present medication cost analysis by drug name and prescriber
4. THE Visualization Layer SHALL visualize provider utilization and patient volume by specialty
5. THE Visualization Layer SHALL enable filtering by date range, department, and insurance type
6. THE Visualization Layer SHALL refresh automatically after each successful pipeline execution

### Requirement 8

**User Story:** As a data engineer, I want the ETL System to maintain comprehensive logging and error handling, so that I can quickly diagnose and resolve pipeline issues

#### Acceptance Criteria

1. THE ETL System SHALL log all pipeline activities with timestamps, task names, and status
2. THE ETL System SHALL capture detailed error messages and stack traces for failed tasks
3. THE ETL System SHALL implement structured logging in JSON format for easy parsing
4. THE ETL System SHALL store logs in a centralized location accessible for analysis
5. WHEN critical errors occur, THEN THE ETL System SHALL trigger immediate alerts via email or Slack

### Requirement 9

**User Story:** As a data engineer, I want the pipeline to be configurable through environment variables and configuration files, so that I can deploy to different environments without code changes

#### Acceptance Criteria

1. THE ETL System SHALL read database connection strings from environment variables
2. THE ETL System SHALL load pipeline configuration (file paths, schedules, thresholds) from YAML files
3. THE ETL System SHALL support separate configurations for development, staging, and production environments
4. THE ETL System SHALL validate configuration parameters at pipeline startup
5. THE ETL System SHALL provide default values for optional configuration parameters
