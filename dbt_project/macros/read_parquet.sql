{% macro read_parquet(table_name, run_date=None) %}
    {%- if run_date is none -%}
        {%- set run_date = modules.datetime.date.today().strftime('%Y-%m-%d') -%}
    {%- endif -%}
    
    {%- set silver_path = env_var('SILVER_DATA_PATH', '/opt/airflow/data/silver') -%}
    {%- set parquet_file = silver_path ~ '/' ~ run_date ~ '/' ~ table_name ~ '.parquet' -%}
    
    -- Note: This assumes the Parquet files have been loaded into external tables
    -- or temporary tables by the ETL pipeline before dbt runs
    {{ table_name }}
{% endmacro %}
