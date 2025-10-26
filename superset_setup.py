"""
Superset Setup Script

This script configures Apache Superset with:
- Database connection to healthcare_warehouse
- Datasets for all dimension and fact tables
- Calculated columns for analytics
- Dashboard configurations

Usage:
    python superset_setup.py --action [setup|test|cleanup]
    
Environment Variables:
    POSTGRES_HOST: PostgreSQL host (default: warehouse-db)
    POSTGRES_PORT: PostgreSQL port (default: 5432)
    POSTGRES_DB: Database name (default: healthcare_warehouse)
    POSTGRES_USER: Database user (default: etl_user)
    POSTGRES_PASSWORD: Database password
    SUPERSET_URL: Superset URL (default: http://localhost:8088)
    SUPERSET_USERNAME: Superset admin username (default: admin)
    SUPERSET_PASSWORD: Superset admin password (default: admin)
"""

import os
import sys
import json
import argparse
import requests
from typing import Dict, List, Optional
import time


class SupersetConfigurator:
    """Configure Superset dashboards and datasets"""
    
    def __init__(
        self,
        superset_url: str = None,
        username: str = None,
        password: str = None
    ):
        self.superset_url = superset_url or os.getenv('SUPERSET_URL', 'http://localhost:8088')
        self.username = username or os.getenv('SUPERSET_USERNAME', 'admin')
        self.password = password or os.getenv('SUPERSET_PASSWORD', 'admin')
        self.session = requests.Session()
        self.access_token = None
        self.csrf_token = None
        
    def login(self) -> bool:
        """
        Authenticate with Superset and get access token
        
        Returns:
            bool: True if login successful
        """
        print(f"Logging in to Superset at {self.superset_url}...")
        
        try:
            # Get CSRF token
            response = self.session.get(f"{self.superset_url}/api/v1/security/csrf_token/")
            if response.status_code == 200:
                self.csrf_token = response.json().get('result')
                self.session.headers.update({
                    'X-CSRFToken': self.csrf_token,
                    'Referer': self.superset_url
                })
            
            # Login to get access token
            login_data = {
                'username': self.username,
                'password': self.password,
                'provider': 'db',
                'refresh': True
            }
            
            response = self.session.post(
                f"{self.superset_url}/api/v1/security/login",
                json=login_data
            )
            
            if response.status_code == 200:
                result = response.json()
                self.access_token = result.get('access_token')
                self.session.headers.update({
                    'Authorization': f'Bearer {self.access_token}'
                })
                print("✓ Successfully logged in to Superset")
                return True
            else:
                print(f"✗ Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"✗ Login error: {str(e)}")
            return False
    
    def test_connection(self) -> bool:
        """
        Test connection to Superset
        
        Returns:
            bool: True if connection successful
        """
        print(f"Testing connection to Superset at {self.superset_url}...")
        
        try:
            response = self.session.get(f"{self.superset_url}/health")
            if response.status_code == 200:
                print("✓ Superset is healthy and accessible")
                return True
            else:
                print(f"✗ Superset health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ Connection error: {str(e)}")
            return False
    
    def create_database_connection(self) -> Optional[int]:
        """
        Create PostgreSQL database connection in Superset
        
        Returns:
            int: Database ID if successful, None otherwise
        """
        print("Creating database connection to healthcare_warehouse...")
        
        # Database connection parameters
        db_host = os.getenv('POSTGRES_HOST', 'warehouse-db')
        db_port = os.getenv('POSTGRES_PORT', '5432')
        db_name = os.getenv('POSTGRES_DB', 'healthcare_warehouse')
        db_user = os.getenv('POSTGRES_USER', 'etl_user')
        db_password = os.getenv('POSTGRES_PASSWORD', 'etl_password')
        
        # SQLAlchemy connection string
        sqlalchemy_uri = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        
        database_config = {
            'database_name': 'Healthcare Warehouse',
            'sqlalchemy_uri': sqlalchemy_uri,
            'expose_in_sqllab': True,
            'allow_run_async': True,
            'allow_ctas': False,
            'allow_cvas': False,
            'allow_dml': False,
            'allow_file_upload': False,
            'extra': json.dumps({
                'metadata_params': {},
                'engine_params': {
                    'connect_args': {
                        'connect_timeout': 10
                    }
                },
                'metadata_cache_timeout': {},
                'schemas_allowed_for_file_upload': []
            })
        }
        
        try:
            # Check if database already exists
            response = self.session.get(f"{self.superset_url}/api/v1/database/")
            if response.status_code == 200:
                databases = response.json().get('result', [])
                for db in databases:
                    if db.get('database_name') == 'Healthcare Warehouse':
                        db_id = db.get('id')
                        print(f"✓ Database connection already exists (ID: {db_id})")
                        return db_id
            
            # Create new database connection
            response = self.session.post(
                f"{self.superset_url}/api/v1/database/",
                json=database_config
            )
            
            if response.status_code == 201:
                db_id = response.json().get('id')
                print(f"✓ Database connection created successfully (ID: {db_id})")
                return db_id
            else:
                print(f"✗ Failed to create database connection: {response.status_code}")
                print(f"  Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"✗ Error creating database connection: {str(e)}")
            return None
    
    def test_database_connection(self, database_id: int) -> bool:
        """
        Test the database connection and verify access to Gold layer tables
        
        Args:
            database_id: Superset database ID
            
        Returns:
            bool: True if connection test successful
        """
        print(f"Testing database connection (ID: {database_id})...")
        
        try:
            # Test connection
            response = self.session.post(
                f"{self.superset_url}/api/v1/database/{database_id}/test_connection"
            )
            
            if response.status_code == 200:
                print("✓ Database connection test successful")
            else:
                print(f"⚠ Database connection test returned: {response.status_code}")
            
            # Verify access to Gold layer tables
            tables_to_verify = [
                'dim_patient', 'dim_provider', 'dim_diagnosis', 
                'dim_procedure', 'dim_medication', 'dim_date',
                'fact_encounter', 'fact_billing', 'fact_lab_test', 'fact_denial'
            ]
            
            # Get list of tables from database
            response = self.session.get(
                f"{self.superset_url}/api/v1/database/{database_id}/tables/"
            )
            
            if response.status_code == 200:
                available_tables = response.json().get('result', [])
                table_names = [t.get('value') for t in available_tables]
                
                print(f"\nVerifying access to Gold layer tables:")
                missing_tables = []
                for table in tables_to_verify:
                    if table in table_names:
                        print(f"  ✓ {table}")
                    else:
                        print(f"  ✗ {table} (not found)")
                        missing_tables.append(table)
                
                if missing_tables:
                    print(f"\n⚠ Warning: {len(missing_tables)} tables not found")
                    print(f"  Missing: {', '.join(missing_tables)}")
                    print(f"  This may be expected if the ETL pipeline hasn't run yet")
                    return False
                else:
                    print(f"\n✓ All {len(tables_to_verify)} Gold layer tables are accessible")
                    return True
            else:
                print(f"✗ Failed to retrieve table list: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"✗ Error testing database connection: {str(e)}")
            return False
    
    def get_database_id(self) -> Optional[int]:
        """
        Get the database ID for Healthcare Warehouse
        
        Returns:
            int: Database ID if found, None otherwise
        """
        try:
            response = self.session.get(f"{self.superset_url}/api/v1/database/")
            if response.status_code == 200:
                databases = response.json().get('result', [])
                for db in databases:
                    if db.get('database_name') == 'Healthcare Warehouse':
                        return db.get('id')
            return None
        except Exception as e:
            print(f"✗ Error getting database ID: {str(e)}")
            return None
    
    def cleanup_database_connection(self) -> bool:
        """
        Remove the Healthcare Warehouse database connection
        
        Returns:
            bool: True if cleanup successful
        """
        print("Cleaning up database connection...")
        
        try:
            db_id = self.get_database_id()
            if not db_id:
                print("✓ No database connection to clean up")
                return True
            
            response = self.session.delete(
                f"{self.superset_url}/api/v1/database/{db_id}"
            )
            
            if response.status_code in [200, 204]:
                print(f"✓ Database connection removed (ID: {db_id})")
                return True
            else:
                print(f"✗ Failed to remove database connection: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"✗ Error during cleanup: {str(e)}")
            return False


def main():
    """Main entry point for Superset setup script"""
    
    parser = argparse.ArgumentParser(
        description='Configure Apache Superset for Healthcare ETL Pipeline'
    )
    parser.add_argument(
        '--action',
        choices=['setup', 'test', 'cleanup', 'setup-datasets'],
        default='setup',
        help='Action to perform (default: setup)'
    )
    parser.add_argument(
        '--superset-url',
        help='Superset URL (default: http://localhost:8088)'
    )
    parser.add_argument(
        '--username',
        help='Superset admin username (default: admin)'
    )
    parser.add_argument(
        '--password',
        help='Superset admin password (default: admin)'
    )
    parser.add_argument(
        '--wait',
        type=int,
        default=0,
        help='Wait N seconds before starting (useful for container startup)'
    )
    
    args = parser.parse_args()
    
    # Wait if requested (useful when running in Docker)
    if args.wait > 0:
        print(f"Waiting {args.wait} seconds for services to start...")
        time.sleep(args.wait)
    
    # Create configurator
    configurator = SupersetConfigurator(
        superset_url=args.superset_url,
        username=args.username,
        password=args.password
    )
    
    # Test connection to Superset
    if not configurator.test_connection():
        print("\n✗ Cannot connect to Superset. Please ensure:")
        print("  1. Superset is running (docker-compose up -d)")
        print("  2. Superset URL is correct")
        print("  3. Network connectivity is available")
        sys.exit(1)
    
    # Login to Superset
    if not configurator.login():
        print("\n✗ Cannot login to Superset. Please check credentials.")
        sys.exit(1)
    
    print(f"\n{'='*60}")
    print(f"Action: {args.action.upper()}")
    print(f"{'='*60}\n")
    
    if args.action == 'setup':
        # Create database connection
        db_id = configurator.create_database_connection()
        if not db_id:
            print("\n✗ Failed to create database connection")
            sys.exit(1)
        
        # Test database connection
        configurator.test_database_connection(db_id)
        
        print(f"\n{'='*60}")
        print("✓ Superset database connection setup complete!")
        print(f"{'='*60}")
        print(f"\nDatabase ID: {db_id}")
        print(f"Database Name: Healthcare Warehouse")
        print(f"\nNext steps:")
        print(f"  1. Access Superset at {configurator.superset_url}")
        print(f"  2. Login with username: {configurator.username}")
        print(f"  3. Navigate to Data > Databases to verify connection")
        print(f"  4. Run the ETL pipeline to populate Gold layer tables")
        print(f"  5. Continue with dataset and dashboard creation")
        
    elif args.action == 'test':
        # Test existing database connection
        db_id = configurator.get_database_id()
        if not db_id:
            print("\n✗ Database connection not found. Run with --action setup first.")
            sys.exit(1)
        
        success = configurator.test_database_connection(db_id)
        if success:
            print(f"\n✓ Database connection test passed")
        else:
            print(f"\n⚠ Database connection test completed with warnings")
            print(f"  Run the ETL pipeline to populate tables if needed")
        
    elif args.action == 'setup-datasets':
        # Create datasets for all tables
        db_id = configurator.get_database_id()
        if not db_id:
            print("\n✗ Database connection not found. Run with --action setup first.")
            sys.exit(1)
        
        dataset_ids = configurator.create_all_datasets(db_id)
        
        print(f"\n{'='*60}")
        print("✓ Superset datasets setup complete!")
        print(f"{'='*60}")
        print(f"\nCreated {len(dataset_ids)} datasets:")
        for table, ds_id in dataset_ids.items():
            print(f"  - {table} (ID: {ds_id})")
        print(f"\nNext steps:")
        print(f"  1. Access Superset at {configurator.superset_url}")
        print(f"  2. Navigate to Data > Datasets to verify")
        print(f"  3. Create charts and dashboards using these datasets")
        
    elif args.action == 'cleanup':
        # Remove datasets and database connection
        configurator.cleanup_datasets()
        success = configurator.cleanup_database_connection()
        if success:
            print(f"\n✓ Cleanup complete")
        else:
            print(f"\n✗ Cleanup failed")
            sys.exit(1)
    
    print()


if __name__ == '__main__':
    main()


    def create_dataset(
        self,
        database_id: int,
        table_name: str,
        schema: str = 'public'
    ) -> Optional[int]:
        """
        Create a Superset dataset for a table
        
        Args:
            database_id: Superset database ID
            table_name: Name of the table
            schema: Database schema (default: public)
            
        Returns:
            int: Dataset ID if successful, None otherwise
        """
        print(f"Creating dataset for {table_name}...")
        
        dataset_config = {
            'database': database_id,
            'schema': schema,
            'table_name': table_name,
            'owners': []
        }
        
        try:
            # Check if dataset already exists
            response = self.session.get(
                f"{self.superset_url}/api/v1/dataset/",
                params={'q': json.dumps({'filters': [{'col': 'table_name', 'opr': 'eq', 'value': table_name}]})}
            )
            
            if response.status_code == 200:
                datasets = response.json().get('result', [])
                if datasets:
                    dataset_id = datasets[0].get('id')
                    print(f"  ✓ Dataset already exists (ID: {dataset_id})")
                    return dataset_id
            
            # Create new dataset
            response = self.session.post(
                f"{self.superset_url}/api/v1/dataset/",
                json=dataset_config
            )
            
            if response.status_code == 201:
                dataset_id = response.json().get('id')
                print(f"  ✓ Dataset created (ID: {dataset_id})")
                return dataset_id
            else:
                print(f"  ✗ Failed to create dataset: {response.status_code}")
                print(f"    Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"  ✗ Error creating dataset: {str(e)}")
            return None
    
    def add_calculated_column(
        self,
        dataset_id: int,
        column_name: str,
        expression: str,
        verbose_name: str = None,
        description: str = None
    ) -> bool:
        """
        Add a calculated column to a dataset
        
        Args:
            dataset_id: Superset dataset ID
            column_name: Name of the calculated column
            expression: SQL expression for the column
            verbose_name: Display name for the column
            description: Description of the column
            
        Returns:
            bool: True if successful
        """
        print(f"  Adding calculated column: {column_name}...")
        
        column_config = {
            'column_name': column_name,
            'expression': expression,
            'verbose_name': verbose_name or column_name,
            'description': description or ''
        }
        
        try:
            response = self.session.post(
                f"{self.superset_url}/api/v1/dataset/{dataset_id}/column/",
                json=column_config
            )
            
            if response.status_code == 201:
                print(f"    ✓ Calculated column added")
                return True
            else:
                print(f"    ⚠ Could not add calculated column: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"    ✗ Error adding calculated column: {str(e)}")
            return False
    
    def configure_column_formatting(
        self,
        dataset_id: int,
        column_name: str,
        column_type: str = None,
        format_string: str = None
    ) -> bool:
        """
        Configure formatting for a dataset column
        
        Args:
            dataset_id: Superset dataset ID
            column_name: Name of the column
            column_type: Column type (e.g., 'NUMERIC', 'TEMPORAL')
            format_string: Format string (e.g., '$,.2f' for currency)
            
        Returns:
            bool: True if successful
        """
        # Note: Column formatting in Superset is typically done through the UI
        # or by updating the dataset metadata. This is a placeholder for
        # future implementation using the dataset update API
        return True
    
    def create_all_datasets(self, database_id: int) -> Dict[str, int]:
        """
        Create datasets for all dimension and fact tables
        
        Args:
            database_id: Superset database ID
            
        Returns:
            dict: Mapping of table names to dataset IDs
        """
        print("\nCreating datasets for all Gold layer tables...")
        
        # Define all tables with their calculated columns
        tables_config = {
            'dim_patient': {
                'calculated_columns': []
            },
            'dim_provider': {
                'calculated_columns': []
            },
            'dim_diagnosis': {
                'calculated_columns': []
            },
            'dim_procedure': {
                'calculated_columns': []
            },
            'dim_medication': {
                'calculated_columns': []
            },
            'dim_date': {
                'calculated_columns': []
            },
            'fact_encounter': {
                'calculated_columns': []
            },
            'fact_billing': {
                'calculated_columns': [
                    {
                        'column_name': 'collection_rate',
                        'expression': 'CASE WHEN billed_amount > 0 THEN (paid_amount / billed_amount) * 100 ELSE 0 END',
                        'verbose_name': 'Collection Rate (%)',
                        'description': 'Percentage of billed amount that was collected'
                    },
                    {
                        'column_name': 'denial_rate',
                        'expression': 'CASE WHEN billed_amount > 0 THEN (denied_amount / billed_amount) * 100 ELSE 0 END',
                        'verbose_name': 'Denial Rate (%)',
                        'description': 'Percentage of billed amount that was denied'
                    },
                    {
                        'column_name': 'outstanding_amount',
                        'expression': 'billed_amount - paid_amount - denied_amount',
                        'verbose_name': 'Outstanding Amount',
                        'description': 'Amount still outstanding (not paid or denied)'
                    }
                ]
            },
            'fact_lab_test': {
                'calculated_columns': []
            },
            'fact_denial': {
                'calculated_columns': []
            }
        }
        
        dataset_ids = {}
        
        for table_name, config in tables_config.items():
            # Create dataset
            dataset_id = self.create_dataset(database_id, table_name)
            if dataset_id:
                dataset_ids[table_name] = dataset_id
                
                # Add calculated columns
                for calc_col in config.get('calculated_columns', []):
                    self.add_calculated_column(
                        dataset_id=dataset_id,
                        column_name=calc_col['column_name'],
                        expression=calc_col['expression'],
                        verbose_name=calc_col.get('verbose_name'),
                        description=calc_col.get('description')
                    )
        
        print(f"\n✓ Created {len(dataset_ids)} datasets")
        return dataset_ids
    
    def cleanup_datasets(self) -> bool:
        """
        Remove all datasets for Healthcare Warehouse
        
        Returns:
            bool: True if cleanup successful
        """
        print("Cleaning up datasets...")
        
        try:
            # Get all datasets
            response = self.session.get(f"{self.superset_url}/api/v1/dataset/")
            if response.status_code != 200:
                print(f"✗ Failed to retrieve datasets: {response.status_code}")
                return False
            
            datasets = response.json().get('result', [])
            
            # Filter datasets for our tables
            table_names = [
                'dim_patient', 'dim_provider', 'dim_diagnosis', 
                'dim_procedure', 'dim_medication', 'dim_date',
                'fact_encounter', 'fact_billing', 'fact_lab_test', 'fact_denial'
            ]
            
            deleted_count = 0
            for dataset in datasets:
                if dataset.get('table_name') in table_names:
                    dataset_id = dataset.get('id')
                    response = self.session.delete(
                        f"{self.superset_url}/api/v1/dataset/{dataset_id}"
                    )
                    if response.status_code in [200, 204]:
                        deleted_count += 1
                        print(f"  ✓ Deleted dataset: {dataset.get('table_name')}")
            
            print(f"✓ Cleaned up {deleted_count} datasets")
            return True
            
        except Exception as e:
            print(f"✗ Error during dataset cleanup: {str(e)}")
            return False
