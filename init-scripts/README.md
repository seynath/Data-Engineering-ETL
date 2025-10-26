# Database Initialization Scripts

This directory contains SQL scripts for initializing the healthcare warehouse PostgreSQL database with the Gold layer star schema.

## Files

### 1. `init-warehouse-db.sql`
Main initialization script that:
- Creates database users (etl_user, analytics_user)
- Grants appropriate permissions
- Calls dimension and fact table creation scripts

### 2. `create_dimension_tables.sql`
Creates all dimension tables:
- `dim_patient` - Patient dimension with SCD Type 2 support
- `dim_provider` - Provider/physician dimension
- `dim_date` - Date dimension (populated separately)
- `dim_diagnosis` - Diagnosis codes dimension
- `dim_procedure` - Procedure codes dimension
- `dim_medication` - Medication dimension

### 3. `create_fact_tables.sql`
Creates all fact tables:
- `fact_encounter` - Patient encounters/visits
- `fact_billing` - Claims and billing information
- `fact_lab_test` - Laboratory test results
- `fact_denial` - Claim denials and appeals

## Usage

### Docker Compose (Automatic)
When using Docker Compose, these scripts run automatically on first container startup:

```bash
docker-compose up -d warehouse-db
```

The scripts in this directory are mounted to `/docker-entrypoint-initdb.d/` and executed in alphabetical order.

### Manual Execution
To run scripts manually against an existing database:

```bash
# Connect to PostgreSQL
psql -h localhost -p 5432 -U postgres -d healthcare_warehouse

# Run initialization script
\i init-warehouse-db.sql

# Or run individual scripts
\i create_dimension_tables.sql
\i create_fact_tables.sql
```

### Populate Date Dimension
After creating tables, populate the date dimension:

```bash
# From project root
python populate_dim_date.py
```

This generates date records from 2020-2030 with all required attributes.

## Schema Overview

### Star Schema Design
```
        dim_patient
             |
             |
        fact_encounter ---- dim_provider
        /    |    \
       /     |     \
fact_billing |  fact_lab_test
      |      |
      |   dim_diagnosis
fact_denial  |
          dim_date
```

### Key Features
- **Surrogate keys**: All dimension tables use auto-incrementing surrogate keys
- **SCD Type 2**: dim_patient tracks historical changes with valid_from/valid_to
- **Foreign key constraints**: Enforce referential integrity between facts and dimensions
- **Indexes**: Optimized for common query patterns
- **Audit columns**: Track record creation timestamps

## Database Users

### etl_user
- Full read/write access
- Used by ETL pipeline (Airflow, dbt)
- Password: Set via environment variable

### analytics_user
- Read-only access
- Used by BI tools (Superset)
- Password: Set via environment variable

## Environment Variables

Required environment variables (set in `.env` or Docker Compose):

```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=healthcare_warehouse
POSTGRES_USER=etl_user
POSTGRES_PASSWORD=etl_password
```

## Verification

Check that all tables were created:

```sql
-- List all tables
\dt

-- Check table counts
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;

-- Verify dim_date population
SELECT COUNT(*) FROM dim_date;
-- Should return 4018 records (2020-2030)
```
