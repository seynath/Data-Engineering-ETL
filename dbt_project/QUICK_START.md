# dbt Quick Start Guide

## Setup (One-time)

```bash
# 1. Install dbt
pip install dbt-postgres

# 2. Install packages
cd dbt_project
dbt deps

# 3. Set environment variables
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5433
export POSTGRES_USER=etl_user
export POSTGRES_PASSWORD=etl_password
export POSTGRES_DB=healthcare_warehouse

# 4. Test connection
dbt debug
```

## Daily Workflow

```bash
# 1. Load Silver layer data to PostgreSQL
python load_silver_to_postgres.py

# 2. Run dbt models
cd dbt_project
dbt run

# 3. Run tests
dbt test

# 4. Check results
dbt docs generate
dbt docs serve
```

## Common Commands

```bash
# Run everything
dbt run && dbt test

# Run specific model
dbt run --select fact_encounter

# Run model and dependencies
dbt run --select +fact_encounter

# Run model and downstream models
dbt run --select fact_encounter+

# Full refresh incremental model
dbt run --select fact_encounter --full-refresh

# Run only changed models
dbt run --select state:modified+

# Run tests for specific model
dbt test --select fact_encounter

# Compile without running
dbt compile --select fact_encounter
```

## Model Execution Order

1. **Staging** (views) - Read from Silver schema
2. **Dimensions** (tables) - Create dimension tables
3. **Facts** (incremental) - Create fact tables

dbt automatically determines the correct order based on dependencies.

## Troubleshooting

```bash
# Connection issues
dbt debug

# See compiled SQL
dbt compile --select model_name
cat target/compiled/healthcare_etl/models/path/to/model.sql

# Verbose logging
dbt run --select model_name --debug

# Clear cache
rm -rf target/
dbt clean
```

## Project Structure

```
dbt_project/
├── models/
│   ├── staging/          # Views reading from silver schema
│   │   ├── stg_patients.sql
│   │   ├── stg_encounters.sql
│   │   └── ...
│   ├── dimensions/       # Dimension tables
│   │   ├── dim_patient.sql (SCD Type 2)
│   │   ├── dim_provider.sql
│   │   └── ...
│   └── facts/           # Fact tables (incremental)
│       ├── fact_encounter.sql
│       ├── fact_billing.sql
│       └── ...
├── tests/               # Custom tests
│   ├── assert_referential_integrity.sql
│   └── assert_no_orphaned_records.sql
└── dbt_project.yml      # Configuration
```

## Key Features

- **SCD Type 2**: `dim_patient` tracks historical changes
- **Incremental Loading**: Fact tables only process new data
- **Data Quality Tests**: Generic and custom tests
- **Documentation**: Auto-generated with lineage graphs
