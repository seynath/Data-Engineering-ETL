-- Initialize healthcare warehouse database
-- This script runs automatically when the warehouse-db container starts
-- Note: The database is already created via POSTGRES_DB environment variable

\echo 'Starting healthcare warehouse initialization...'

-- Create read-only user for analytics/reporting (etl_user is created via POSTGRES_USER)
DO
$$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'analytics_user') THEN
        CREATE USER analytics_user WITH PASSWORD 'analytics_password';
        RAISE NOTICE 'Created analytics_user';
    END IF;
END
$$;

-- Grant permissions to etl_user (full access for ETL operations)
GRANT ALL PRIVILEGES ON DATABASE healthcare_warehouse TO etl_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO etl_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO etl_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO etl_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO etl_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO etl_user;

-- Grant read-only permissions to analytics_user
GRANT CONNECT ON DATABASE healthcare_warehouse TO analytics_user;
GRANT USAGE ON SCHEMA public TO analytics_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO analytics_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO analytics_user;

\echo 'User permissions configured successfully'

-- Create dimension tables
\echo 'Creating dimension tables...'
\i /docker-entrypoint-initdb.d/create_dimension_tables.sql

-- Create fact tables
\echo 'Creating fact tables...'
\i /docker-entrypoint-initdb.d/create_fact_tables.sql

\echo 'Healthcare warehouse initialization complete!'
\echo 'Note: Run populate_dim_date.py to populate the date dimension table'
