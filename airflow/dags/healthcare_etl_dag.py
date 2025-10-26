"""
Healthcare ETL Pipeline DAG

This DAG orchestrates the complete ETL pipeline for hospital operational data:
- Bronze Layer: Raw CSV ingestion
- Silver Layer: Data cleaning and transformation to Parquet
- Gold Layer: dbt transformations to star schema
- Data Quality: Great Expectations validation at each layer
- Reporting: Data quality reports and Superset cache refresh

Schedule: Daily at 2:00 AM UTC
Retries: 3 attempts with exponential backoff (5 min initial delay)
Alerts: Email notifications on failure with detailed error information
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.operators.dummy import DummyOperator
from airflow.utils.task_group import TaskGroup
from airflow.utils.email import send_email

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import pipeline modules
from bronze_ingestion import ingest_csv_files, validate_csv_files, BronzeIngestionError
from silver_transformation import transform_bronze_to_silver, SilverTransformationError
from data_quality import DataQualityValidator


def send_failure_alert(context):
    """
    Custom callback function to send detailed failure alerts
    
    Args:
        context: Airflow context dictionary with task instance info
    """
    task_instance = context.get('task_instance')
    dag_id = context.get('dag').dag_id
    task_id = task_instance.task_id
    execution_date = context.get('execution_date')
    exception = context.get('exception')
    log_url = task_instance.log_url
    
    # Build detailed error message
    subject = f"❌ Airflow Task Failed: {dag_id}.{task_id}"
    
    html_content = f"""
    <h2>Airflow Task Failure Alert</h2>
    <p><strong>DAG:</strong> {dag_id}</p>
    <p><strong>Task:</strong> {task_id}</p>
    <p><strong>Execution Date:</strong> {execution_date}</p>
    <p><strong>Try Number:</strong> {task_instance.try_number}</p>
    <p><strong>Max Tries:</strong> {task_instance.max_tries}</p>
    
    <h3>Error Details:</h3>
    <pre>{str(exception)}</pre>
    
    <h3>Actions:</h3>
    <ul>
        <li>Review task logs: <a href="{log_url}">View Logs</a></li>
        <li>Check data quality reports in /opt/airflow/logs/</li>
        <li>Verify source data availability</li>
        <li>Check database connectivity</li>
    </ul>
    
    <p><em>This is an automated alert from the Healthcare ETL Pipeline.</em></p>
    """
    
    try:
        send_email(
            to=context['dag'].default_args['email'],
            subject=subject,
            html_content=html_content
        )
    except Exception as e:
        print(f"Failed to send failure alert email: {str(e)}")


def send_success_alert(context):
    """
    Custom callback function to send success notification with metrics
    
    Args:
        context: Airflow context dictionary with task instance info
    """
    dag_id = context.get('dag').dag_id
    execution_date = context.get('execution_date')
    
    subject = f"✅ Airflow DAG Succeeded: {dag_id}"
    
    html_content = f"""
    <h2>Healthcare ETL Pipeline - Success</h2>
    <p><strong>DAG:</strong> {dag_id}</p>
    <p><strong>Execution Date:</strong> {execution_date}</p>
    <p><strong>Status:</strong> ✅ All tasks completed successfully</p>
    
    <h3>Pipeline Summary:</h3>
    <ul>
        <li>Bronze Layer: CSV files ingested</li>
        <li>Silver Layer: Data cleaned and transformed to Parquet</li>
        <li>Gold Layer: Star schema populated via dbt</li>
        <li>Data Quality: All validations passed</li>
        <li>Reporting: Quality report generated</li>
    </ul>
    
    <p>Data is now available for analysis in Superset dashboards.</p>
    
    <p><em>This is an automated notification from the Healthcare ETL Pipeline.</em></p>
    """
    
    try:
        send_email(
            to=context['dag'].default_args['email'],
            subject=subject,
            html_content=html_content
        )
    except Exception as e:
        print(f"Failed to send success alert email: {str(e)}")


# DAG default arguments with enhanced alerting
default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'email': [os.getenv('ALERT_EMAIL', 'data-team@hospital.com')],
    'email_on_failure': True,
    'email_on_retry': False,
    'email_on_success': False,  # Set to True if you want success emails
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'retry_exponential_backoff': True,
    'max_retry_delay': timedelta(minutes=30),
    'execution_timeout': timedelta(minutes=30),  # Default timeout for all tasks
    'on_failure_callback': send_failure_alert,
}

# Create DAG with scheduling and alerting configuration
dag = DAG(
    'healthcare_etl_pipeline',
    default_args=default_args,
    description='Hospital data ETL with Bronze/Silver/Gold layers',
    schedule_interval='0 2 * * *',  # Daily at 2:00 AM UTC
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['healthcare', 'etl', 'production'],
    max_active_runs=1,  # Prevent concurrent runs
    dagrun_timeout=timedelta(hours=2),  # Maximum DAG run time
    on_success_callback=send_success_alert,  # Alert on successful completion
    on_failure_callback=send_failure_alert,  # Alert on DAG failure
)

# Environment variables
BRONZE_DATA_PATH = os.getenv('BRONZE_DATA_PATH', '/opt/airflow/data/bronze')
SILVER_DATA_PATH = os.getenv('SILVER_DATA_PATH', '/opt/airflow/data/silver')
SOURCE_CSV_PATH = os.getenv('SOURCE_CSV_PATH', '/opt/airflow/dataset')
SILVER_CONFIG_PATH = os.getenv('SILVER_CONFIG_PATH', '/opt/airflow/config/silver_table_config.yaml')

# Table names
TABLE_NAMES = [
    'patients',
    'encounters',
    'diagnoses',
    'procedures',
    'medications',
    'lab_tests',
    'claims_and_billing',
    'providers',
    'denials'
]


# ============================================================================
# BRONZE LAYER TASKS
# ============================================================================

def validate_source_files(**context):
    """
    Validate that all expected CSV files are present before ingestion
    """
    run_date = context['ds']
    
    try:
        validated_files = validate_csv_files(SOURCE_CSV_PATH)
        
        # Push file list to XCom for downstream tasks
        context['task_instance'].xcom_push(
            key='validated_files',
            value=[str(f) for f in validated_files]
        )
        
        print(f"✓ Validated {len(validated_files)} CSV files for run date {run_date}")
        return True
        
    except BronzeIngestionError as e:
        print(f"✗ Validation failed: {str(e)}")
        raise


def ingest_bronze_layer(**context):
    """
    Ingest all CSV files to Bronze layer with metadata generation
    """
    run_date = context['ds']
    
    try:
        row_counts = ingest_csv_files(
            source_dir=SOURCE_CSV_PATH,
            bronze_dir=BRONZE_DATA_PATH,
            run_date=run_date
        )
        
        # Push row counts to XCom
        context['task_instance'].xcom_push(
            key='bronze_row_counts',
            value=row_counts
        )
        
        total_rows = sum(row_counts.values())
        print(f"✓ Ingested {len(row_counts)} files with {total_rows:,} total rows")
        
        return row_counts
        
    except BronzeIngestionError as e:
        print(f"✗ Bronze ingestion failed: {str(e)}")
        raise


def validate_bronze_row_counts(**context):
    """
    Validate Bronze layer row counts match expectations
    """
    run_date = context['ds']
    
    # Get row counts from XCom
    row_counts = context['task_instance'].xcom_pull(
        task_ids='ingest_bronze_layer',
        key='bronze_row_counts'
    )
    
    if not row_counts:
        raise ValueError("No row counts found from Bronze ingestion")
    
    # Validate each table has data
    failed_tables = []
    for table, count in row_counts.items():
        if count == 0:
            failed_tables.append(table)
            print(f"✗ {table}: 0 rows (FAILED)")
        else:
            print(f"✓ {table}: {count:,} rows")
    
    if failed_tables:
        raise ValueError(
            f"Bronze validation failed: {len(failed_tables)} tables have 0 rows: "
            f"{', '.join(failed_tables)}"
        )
    
    print(f"✓ Bronze layer validation passed for {len(row_counts)} tables")
    return True


# Create Bronze layer tasks
with dag:
    start = DummyOperator(
        task_id='start',
        dag=dag
    )
    
    validate_source = PythonOperator(
        task_id='validate_source_files',
        python_callable=validate_source_files,
        provide_context=True,
        execution_timeout=timedelta(minutes=5),  # Quick validation
        dag=dag
    )
    
    ingest_bronze = PythonOperator(
        task_id='ingest_bronze_layer',
        python_callable=ingest_bronze_layer,
        provide_context=True,
        execution_timeout=timedelta(minutes=10),  # File copying
        dag=dag
    )
    
    validate_bronze = PythonOperator(
        task_id='validate_bronze_layer',
        python_callable=validate_bronze_row_counts,
        provide_context=True,
        execution_timeout=timedelta(minutes=5),  # Quick validation
        dag=dag
    )
    
    # ============================================================================
    # SILVER LAYER TASKS
    # ============================================================================
    
    def transform_table_to_silver(table_name, **context):
        """
        Transform a specific Bronze table to Silver Parquet format
        """
        run_date = context['ds']
        
        try:
            result = transform_bronze_to_silver(
                bronze_dir=BRONZE_DATA_PATH,
                silver_dir=SILVER_DATA_PATH,
                config_file=SILVER_CONFIG_PATH,
                run_date=run_date,
                table_name=table_name
            )
            
            if table_name in result:
                print(f"✓ Transformed {table_name} to Silver layer: {result[table_name]}")
                return result[table_name]
            else:
                raise SilverTransformationError(f"Failed to transform {table_name}")
                
        except SilverTransformationError as e:
            print(f"✗ Silver transformation failed for {table_name}: {str(e)}")
            raise
    
    
    def validate_silver_with_great_expectations(**context):
        """
        Run Great Expectations validation on Silver layer
        """
        run_date = context['ds']
        
        try:
            validator = DataQualityValidator(
                context_root_dir='/opt/airflow/great_expectations'
            )
            
            validation_result = validator.validate_silver_layer(run_date)
            
            # Push validation results to XCom
            context['task_instance'].xcom_push(
                key='silver_validation_result',
                value=validation_result
            )
            
            if validation_result['success']:
                print(f"✓ Silver layer validation passed")
                print(f"  Success rate: {validation_result['statistics']['success_percent']:.2f}%")
            else:
                print(f"✗ Silver layer validation failed")
                print(f"  Success rate: {validation_result['statistics']['success_percent']:.2f}%")
                print(f"  Failed validations: {validation_result['statistics']['unsuccessful_validations']}")
                raise ValueError("Silver layer validation failed")
            
            return validation_result
            
        except Exception as e:
            print(f"✗ Silver validation error: {str(e)}")
            raise
    
    
    # Create Silver transformation task group
    with TaskGroup('silver_transformations', tooltip='Transform Bronze to Silver') as silver_group:
        silver_tasks = []
        
        for table in TABLE_NAMES:
            task = PythonOperator(
                task_id=f'transform_{table}',
                python_callable=transform_table_to_silver,
                op_kwargs={'table_name': table},
                provide_context=True,
                execution_timeout=timedelta(minutes=15),  # Transformation timeout per table
                dag=dag
            )
            silver_tasks.append(task)
    
    validate_silver = PythonOperator(
        task_id='validate_silver_layer',
        python_callable=validate_silver_with_great_expectations,
        provide_context=True,
        execution_timeout=timedelta(minutes=20),  # GE validation can take time
        dag=dag
    )
    
    # ============================================================================
    # DBT (GOLD LAYER) TASKS
    # ============================================================================
    
    # dbt project directory
    DBT_PROJECT_DIR = '/opt/airflow/dbt_project'
    DBT_PROFILES_DIR = '/opt/airflow/dbt_project'
    
    # Create dbt task group
    with TaskGroup('dbt_gold_layer', tooltip='dbt transformations for Gold layer') as dbt_group:
        
        dbt_run_staging = BashOperator(
            task_id='dbt_run_staging',
            bash_command=f'cd {DBT_PROJECT_DIR} && dbt run --profiles-dir {DBT_PROFILES_DIR} --select staging.*',
            execution_timeout=timedelta(minutes=15),  # dbt staging models
            dag=dag
        )
        
        dbt_test_staging = BashOperator(
            task_id='dbt_test_staging',
            bash_command=f'cd {DBT_PROJECT_DIR} && dbt test --profiles-dir {DBT_PROFILES_DIR} --select staging.*',
            execution_timeout=timedelta(minutes=10),  # dbt tests
            dag=dag
        )
        
        dbt_run_dimensions = BashOperator(
            task_id='dbt_run_dimensions',
            bash_command=f'cd {DBT_PROJECT_DIR} && dbt run --profiles-dir {DBT_PROFILES_DIR} --select dimensions.*',
            execution_timeout=timedelta(minutes=15),  # dbt dimension models
            dag=dag
        )
        
        dbt_run_facts = BashOperator(
            task_id='dbt_run_facts',
            bash_command=f'cd {DBT_PROJECT_DIR} && dbt run --profiles-dir {DBT_PROFILES_DIR} --select facts.*',
            execution_timeout=timedelta(minutes=20),  # dbt fact models (can be larger)
            dag=dag
        )
        
        dbt_test_gold = BashOperator(
            task_id='dbt_test_gold',
            bash_command=f'cd {DBT_PROJECT_DIR} && dbt test --profiles-dir {DBT_PROFILES_DIR}',
            execution_timeout=timedelta(minutes=15),  # dbt tests
            dag=dag
        )
        
        # Set dbt task dependencies
        dbt_run_staging >> dbt_test_staging >> dbt_run_dimensions >> dbt_run_facts >> dbt_test_gold
    
    # ============================================================================
    # DATA QUALITY AND REPORTING TASKS
    # ============================================================================
    
    def validate_gold_layer(**context):
        """
        Run final validation on Gold layer (optional - can be implemented with GE)
        For now, we'll validate that key tables exist and have data
        """
        import psycopg2
        
        run_date = context['ds']
        
        # Database connection parameters
        conn_params = {
            'host': os.getenv('POSTGRES_HOST', 'warehouse-db'),
            'port': os.getenv('POSTGRES_PORT', '5432'),
            'database': os.getenv('POSTGRES_DB', 'healthcare_warehouse'),
            'user': os.getenv('POSTGRES_USER', 'etl_user'),
            'password': os.getenv('POSTGRES_PASSWORD', 'etl_password')
        }
        
        try:
            conn = psycopg2.connect(**conn_params)
            cursor = conn.cursor()
            
            # Tables to validate
            tables_to_check = [
                'dim_patient', 'dim_provider', 'dim_diagnosis', 
                'dim_procedure', 'dim_medication',
                'fact_encounter', 'fact_billing', 'fact_lab_test', 'fact_denial'
            ]
            
            validation_results = {}
            
            for table in tables_to_check:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                validation_results[table] = count
                
                if count > 0:
                    print(f"✓ {table}: {count:,} rows")
                else:
                    print(f"⚠ {table}: 0 rows (WARNING)")
            
            cursor.close()
            conn.close()
            
            # Push results to XCom
            context['task_instance'].xcom_push(
                key='gold_validation_results',
                value=validation_results
            )
            
            print(f"✓ Gold layer validation completed")
            return validation_results
            
        except Exception as e:
            print(f"✗ Gold layer validation failed: {str(e)}")
            raise
    
    
    def generate_data_quality_report(**context):
        """
        Generate comprehensive data quality report from all validation results
        """
        run_date = context['ds']
        
        try:
            # Get validation results from XCom
            bronze_row_counts = context['task_instance'].xcom_pull(
                task_ids='ingest_bronze_layer',
                key='bronze_row_counts'
            )
            
            silver_validation = context['task_instance'].xcom_pull(
                task_ids='validate_silver_layer',
                key='silver_validation_result'
            )
            
            gold_validation = context['task_instance'].xcom_pull(
                task_ids='validate_gold_layer',
                key='gold_validation_results'
            )
            
            # Create validator instance
            validator = DataQualityValidator(
                context_root_dir='/opt/airflow/great_expectations'
            )
            
            # Compile all validation results
            all_validations = []
            if silver_validation:
                all_validations.append(silver_validation)
            
            # Generate report
            report = validator.generate_data_quality_report(
                validation_results=all_validations,
                output_file='/opt/airflow/logs/data_quality_report.json'
            )
            
            print(f"✓ Data quality report generated")
            print(f"  Overall success rate: {report['aggregate_statistics']['overall_success_rate']:.2f}%")
            
            return report
            
        except Exception as e:
            print(f"✗ Failed to generate data quality report: {str(e)}")
            raise
    
    
    def refresh_superset_cache(**context):
        """
        Refresh Superset cache after successful pipeline completion
        Uses Superset REST API to refresh datasets and clear cache
        """
        import requests
        
        run_date = context['ds']
        
        superset_url = os.getenv('SUPERSET_URL', 'http://superset:8088')
        username = os.getenv('SUPERSET_USERNAME', 'admin')
        password = os.getenv('SUPERSET_PASSWORD', 'admin')
        
        print(f"Refreshing Superset cache for run date {run_date}...")
        
        try:
            # Create session
            session = requests.Session()
            
            # Get CSRF token
            csrf_response = session.get(f"{superset_url}/api/v1/security/csrf_token/")
            if csrf_response.status_code == 200:
                csrf_token = csrf_response.json().get('result')
                session.headers.update({
                    'X-CSRFToken': csrf_token,
                    'Referer': superset_url
                })
            
            # Login to get access token
            login_data = {
                'username': username,
                'password': password,
                'provider': 'db',
                'refresh': True
            }
            
            login_response = session.post(
                f"{superset_url}/api/v1/security/login",
                json=login_data
            )
            
            if login_response.status_code != 200:
                print(f"⚠ Could not login to Superset: {login_response.status_code}")
                print(f"  Superset may not be configured yet. Skipping cache refresh.")
                return True
            
            access_token = login_response.json().get('access_token')
            session.headers.update({
                'Authorization': f'Bearer {access_token}'
            })
            
            # Get all datasets
            datasets_response = session.get(f"{superset_url}/api/v1/dataset/")
            
            if datasets_response.status_code == 200:
                datasets = datasets_response.json().get('result', [])
                
                # Refresh each dataset
                refreshed_count = 0
                for dataset in datasets:
                    dataset_id = dataset.get('id')
                    table_name = dataset.get('table_name')
                    
                    # Refresh dataset metadata
                    refresh_response = session.put(
                        f"{superset_url}/api/v1/dataset/{dataset_id}/refresh"
                    )
                    
                    if refresh_response.status_code in [200, 204]:
                        refreshed_count += 1
                        print(f"  ✓ Refreshed dataset: {table_name}")
                    else:
                        print(f"  ⚠ Could not refresh dataset {table_name}: {refresh_response.status_code}")
                
                print(f"✓ Refreshed {refreshed_count} datasets")
            else:
                print(f"⚠ Could not retrieve datasets: {datasets_response.status_code}")
            
            # Clear cache (if cache API is available)
            try:
                cache_response = session.delete(f"{superset_url}/api/v1/cache/")
                if cache_response.status_code in [200, 204]:
                    print(f"✓ Cleared Superset cache")
            except Exception as e:
                print(f"  ⚠ Could not clear cache: {str(e)}")
            
            print(f"✓ Superset cache refresh completed for run date {run_date}")
            return True
            
        except requests.exceptions.ConnectionError:
            print(f"⚠ Could not connect to Superset at {superset_url}")
            print(f"  Superset may not be running. Skipping cache refresh.")
            return True
        except Exception as e:
            print(f"⚠ Error refreshing Superset cache: {str(e)}")
            print(f"  Continuing pipeline execution...")
            return True
    
    
    validate_gold = PythonOperator(
        task_id='validate_gold_layer',
        python_callable=validate_gold_layer,
        provide_context=True,
        execution_timeout=timedelta(minutes=10),  # Database validation
        dag=dag
    )
    
    generate_report = PythonOperator(
        task_id='generate_data_quality_report',
        python_callable=generate_data_quality_report,
        provide_context=True,
        execution_timeout=timedelta(minutes=5),  # Report generation
        dag=dag
    )
    
    refresh_superset = PythonOperator(
        task_id='refresh_superset_cache',
        python_callable=refresh_superset_cache,
        provide_context=True,
        execution_timeout=timedelta(minutes=5),  # Cache refresh
        dag=dag
    )
    
    end = DummyOperator(
        task_id='end',
        dag=dag
    )
    
    # Set complete task dependencies
    start >> validate_source >> ingest_bronze >> validate_bronze >> silver_group >> validate_silver >> dbt_group >> validate_gold >> generate_report >> refresh_superset >> end
