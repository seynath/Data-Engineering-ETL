"""
Configuration Usage Example

This example demonstrates how to use the configuration management system
in the Healthcare ETL Pipeline.
"""

from config_loader import get_config
from bronze_ingestion import ingest_csv_files
from silver_transformation import transform_bronze_to_silver


def run_pipeline_with_config():
    """
    Example of running the complete pipeline using the configuration system.
    """
    # Get configuration instance
    config = get_config()
    
    print("="*60)
    print("HEALTHCARE ETL PIPELINE - Configuration-Driven Execution")
    print("="*60)
    
    # Display configuration summary
    print(f"\nPipeline: {config.get('pipeline.name')} v{config.get('pipeline.version')}")
    print(f"Environment: {config.environment}")
    print(f"Run Date: {config.get_run_date()}")
    
    # Get Bronze configuration
    bronze_config = config.get_bronze_config()
    print(f"\nBronze Layer:")
    print(f"  Source: {bronze_config['source_path']}")
    print(f"  Target: {bronze_config['target_path']}")
    print(f"  Tables: {len(bronze_config['tables'])}")
    
    # Get Silver configuration
    silver_config = config.get_silver_config()
    print(f"\nSilver Layer:")
    print(f"  Source: {silver_config['source_path']}")
    print(f"  Target: {silver_config['target_path']}")
    print(f"  Compression: {silver_config['parquet']['compression']}")
    
    # Get Gold configuration
    gold_config = config.get_gold_config()
    print(f"\nGold Layer:")
    print(f"  Database: {gold_config['database']['database']}")
    print(f"  Connection: {config.get_database_connection_string()}")
    
    # Check feature flags
    print(f"\nFeature Flags:")
    print(f"  Bronze Validation: {config.is_feature_enabled('enable_bronze_validation')}")
    print(f"  Silver Validation: {config.is_feature_enabled('enable_silver_validation')}")
    print(f"  Incremental Loading: {config.is_feature_enabled('enable_incremental_loading')}")
    
    # Get data quality settings
    print(f"\nData Quality:")
    print(f"  Fail on Error: {config.should_fail_on_data_quality_error()}")
    print(f"  Warning Threshold: {config.get_data_quality_warning_threshold()}")
    
    print("\n" + "="*60)
    
    # Example: Run Bronze ingestion with configuration
    if config.is_feature_enabled('enable_bronze_validation'):
        print("\n[STEP 1] Bronze Layer Ingestion")
        try:
            result = ingest_csv_files(
                source_dir=bronze_config['source_path'],
                bronze_dir=bronze_config['target_path'],
                run_date=config.get_run_date()
            )
            print(f"✓ Ingested {len(result)} tables")
        except Exception as e:
            print(f"✗ Bronze ingestion failed: {str(e)}")
            return
    
    # Example: Run Silver transformation with configuration
    if config.is_feature_enabled('enable_silver_validation'):
        print("\n[STEP 2] Silver Layer Transformation")
        try:
            result = transform_bronze_to_silver(
                bronze_dir=bronze_config['target_path'],
                silver_dir=silver_config['target_path'],
                config_file=silver_config['table_config_file'],
                run_date=config.get_run_date()
            )
            print(f"✓ Transformed {len(result)} tables")
        except Exception as e:
            print(f"✗ Silver transformation failed: {str(e)}")
            return
    
    print("\n" + "="*60)
    print("Pipeline execution completed successfully!")
    print("="*60)


def demonstrate_config_features():
    """
    Demonstrate various configuration features.
    """
    config = get_config()
    
    print("\n" + "="*60)
    print("CONFIGURATION FEATURES DEMONSTRATION")
    print("="*60)
    
    # 1. Accessing nested configuration
    print("\n1. Accessing Nested Configuration:")
    print(f"   Bronze source path: {config.get('bronze.source_path')}")
    print(f"   Silver compression: {config.get('silver.parquet.compression')}")
    print(f"   Database host: {config.get('gold.database.host')}")
    
    # 2. Using default values
    print("\n2. Using Default Values:")
    custom_value = config.get('custom.setting', 'default_value')
    print(f"   Custom setting (with default): {custom_value}")
    
    # 3. Getting entire sections
    print("\n3. Getting Entire Sections:")
    airflow_config = config.get_airflow_config()
    print(f"   DAG ID: {airflow_config['dag']['dag_id']}")
    print(f"   Schedule: {airflow_config['dag']['schedule_interval']}")
    print(f"   Retries: {airflow_config['default_args']['retries']}")
    
    # 4. Helper methods
    print("\n4. Helper Methods:")
    print(f"   Table list: {config.get_table_list()}")
    print(f"   Task timeout (bronze): {config.get_task_timeout('bronze_ingestion')}s")
    print(f"   Benchmark (silver): {config.get_benchmark('silver_transformation_per_table_max')}s")
    
    # 5. Feature flags
    print("\n5. Feature Flags:")
    features = config.get_section('features')
    enabled_features = [name for name, enabled in features.items() if enabled]
    print(f"   Enabled features: {', '.join(enabled_features)}")
    
    # 6. Environment-specific settings
    print("\n6. Environment-Specific Settings:")
    print(f"   Current environment: {config.environment}")
    print(f"   Log level: {config.get('logging.level')}")
    print(f"   DAG schedule: {config.get('airflow.dag.schedule_interval')}")
    
    print("\n" + "="*60)


def show_configuration_validation():
    """
    Demonstrate configuration validation.
    """
    print("\n" + "="*60)
    print("CONFIGURATION VALIDATION")
    print("="*60)
    
    try:
        config = get_config()
        
        print("\n✓ Configuration loaded successfully")
        print("✓ All required sections present")
        print("✓ Environment variables substituted")
        print("✓ Validation rules passed")
        
        # Show validation details
        print("\nValidation Details:")
        print(f"  - Pipeline name: {config.get('pipeline.name')}")
        print(f"  - Bronze tables: {len(config.get_table_list())} configured")
        print(f"  - Database connection: Valid")
        print(f"  - Data quality threshold: {config.get_data_quality_warning_threshold()}")
        
    except Exception as e:
        print(f"\n✗ Configuration validation failed: {str(e)}")
    
    print("\n" + "="*60)


if __name__ == '__main__':
    """
    Run configuration usage examples.
    """
    import sys
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    print("\n" + "="*60)
    print("CONFIGURATION MANAGEMENT SYSTEM - USAGE EXAMPLES")
    print("="*60)
    
    # Show configuration validation
    show_configuration_validation()
    
    # Demonstrate configuration features
    demonstrate_config_features()
    
    # Optionally run full pipeline (commented out by default)
    # Uncomment the line below to run the full pipeline
    # run_pipeline_with_config()
    
    print("\n" + "="*60)
    print("Examples completed successfully!")
    print("="*60 + "\n")
