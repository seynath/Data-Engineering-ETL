# Healthcare ETL dbt Project

This dbt project transforms Silver layer data (Parquet files) into Gold layer analytics tables (PostgreSQL star schema).

## Project Structure

```
dbt_project/
├── models/
│   ├── staging/          # Staging models reading from Silver Parquet files
│   ├── dimensions/       # Dimension table models
│   └── facts/           # Fact table models
├── tests/               # Custom data quality tests
├── macros/              # Reusable SQL macros
└── dbt_project.yml      # Project configuration
```

## Setup

1. Install dbt-postgres:
```bash
pip install dbt-postgres
```

2. Configure environment variables:
```bash
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5433
export POSTGRES_USER=etl_user
export POSTGRES_PASSWORD=etl_password
export POSTGRES_DB=healthcare_warehouse
```

3. Test connection:
```bash
cd dbt_project
dbt debug
```

## Running dbt

### Run all models
```bash
dbt run
```

### Run specific model groups
```bash
dbt run --select staging.*
dbt run --select dimensions.*
dbt run --select facts.*
```

### Run tests
```bash
dbt test
```

### Generate documentation
```bash
dbt docs generate
dbt docs serve
```

## Model Materialization Strategy

- **Staging models**: Materialized as views (lightweight, always fresh)
- **Dimension models**: Materialized as tables (static reference data)
- **Fact models**: Materialized as incremental tables (optimized for large datasets)

## Data Flow

```
Silver Parquet Files → Staging Models → Dimension/Fact Models → Gold Layer Tables
```
