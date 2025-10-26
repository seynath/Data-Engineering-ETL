"""
Load Silver layer Parquet files into PostgreSQL staging tables for dbt processing.

This script reads Parquet files from the Silver layer and loads them into
PostgreSQL tables that dbt can query as sources.
"""

import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, DatabaseError

# Import centralized logger
from logger import get_logger

# Configure logging
logger = get_logger(__name__)


def get_db_connection_string():
    """
    Get PostgreSQL connection string from environment variables.
    
    Returns:
        Connection string for PostgreSQL
    
    Raises:
        ValueError: If required environment variables are missing
    """
    try:
        host = os.getenv('POSTGRES_HOST', 'localhost')
        port = os.getenv('POSTGRES_PORT', '5433')
        database = os.getenv('POSTGRES_DB', 'healthcare_warehouse')
        user = os.getenv('POSTGRES_USER', 'etl_user')
        password = os.getenv('POSTGRES_PASSWORD', 'etl_password')
        
        # Validate required parameters
        if not all([host, port, database, user, password]):
            raise ValueError("Missing required database connection parameters")
        
        connection_string = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        
        logger.debug(
            "Database connection string created",
            metadata={'host': host, 'port': port, 'database': database, 'user': user}
        )
        
        return connection_string
    
    except Exception as e:
        error_msg = f"Failed to create database connection string: {str(e)}"
        logger.error(error_msg, metadata={'error': str(e)})
        raise ValueError(error_msg) from e


def create_staging_schema(engine, max_retries=3, retry_delay=5):
    """
    Create staging schema if it doesn't exist with retry logic.
    
    Args:
        engine: SQLAlchemy engine
        max_retries: Maximum number of retry attempts
        retry_delay: Delay in seconds between retries
    
    Raises:
        RuntimeError: If schema creation fails after all retries
    """
    for attempt in range(1, max_retries + 1):
        try:
            with engine.begin() as conn:
                conn.execute(text("CREATE SCHEMA IF NOT EXISTS silver"))
            
            logger.info(
                "Staging schema 'silver' created or already exists",
                metadata={'attempt': attempt}
            )
            return
        
        except OperationalError as e:
            error_msg = f"Database connection error creating schema (attempt {attempt}/{max_retries}): {str(e)}"
            logger.warning(error_msg, metadata={'attempt': attempt, 'max_retries': max_retries, 'error': str(e)})
            
            if attempt < max_retries:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error("Max retries reached for schema creation")
                raise RuntimeError(f"Failed to create schema after {max_retries} attempts") from e
        
        except Exception as e:
            error_msg = f"Unexpected error creating schema: {str(e)}"
            logger.error(error_msg, metadata={'error': str(e), 'traceback': traceback.format_exc()})
            raise RuntimeError(error_msg) from e


def load_parquet_to_postgres(parquet_file, table_name, engine, if_exists='replace', max_retries=3, retry_delay=5):
    """
    Load a Parquet file into PostgreSQL with retry logic.
    
    Args:
        parquet_file: Path to the Parquet file
        table_name: Name of the target table
        engine: SQLAlchemy engine
        if_exists: How to behave if table exists ('replace', 'append', 'fail')
        max_retries: Maximum number of retry attempts
        retry_delay: Delay in seconds between retries
    
    Returns:
        Number of rows loaded
    
    Raises:
        RuntimeError: If loading fails after all retries
    """
    start_time = datetime.now()
    
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(
                f"Loading {parquet_file} into table silver.{table_name} (attempt {attempt}/{max_retries})",
                metadata={'parquet_file': str(parquet_file), 'table_name': table_name, 'attempt': attempt}
            )
            
            # Read Parquet file
            try:
                df = pd.read_parquet(parquet_file)
                row_count = len(df)
                column_count = len(df.columns)
                logger.info(
                    f"Read {row_count} rows from {parquet_file}",
                    metadata={'row_count': row_count, 'column_count': column_count}
                )
            except FileNotFoundError as e:
                error_msg = f"Parquet file not found: {parquet_file}"
                logger.error(error_msg, metadata={'parquet_file': str(parquet_file), 'error': str(e)})
                raise RuntimeError(error_msg) from e
            except Exception as e:
                error_msg = f"Failed to read Parquet file {parquet_file}: {str(e)}"
                logger.error(error_msg, metadata={'parquet_file': str(parquet_file), 'error': str(e)})
                raise RuntimeError(error_msg) from e
            
            # Convert date columns to proper format
            try:
                date_columns = df.select_dtypes(include=['datetime64']).columns
                for col in date_columns:
                    df[col] = pd.to_datetime(df[col]).dt.date
                
                if len(date_columns) > 0:
                    logger.debug(f"Converted {len(date_columns)} date columns")
            except Exception as e:
                logger.warning(f"Error converting date columns: {str(e)}", metadata={'error': str(e)})
            
            # Load to PostgreSQL
            try:
                df.to_sql(
                    name=table_name,
                    con=engine,
                    schema='silver',
                    if_exists=if_exists,
                    index=False,
                    method='multi',
                    chunksize=1000
                )
            except OperationalError as e:
                error_msg = f"Database connection error loading {table_name} (attempt {attempt}/{max_retries}): {str(e)}"
                logger.warning(error_msg, metadata={'table_name': table_name, 'attempt': attempt, 'error': str(e)})
                
                if attempt < max_retries:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    continue
                else:
                    logger.error(f"Max retries reached for loading {table_name}")
                    raise RuntimeError(f"Failed to load {table_name} after {max_retries} attempts") from e
            
            except DatabaseError as e:
                error_msg = f"Database error loading {table_name}: {str(e)}"
                logger.error(error_msg, metadata={'table_name': table_name, 'error': str(e), 'traceback': traceback.format_exc()})
                raise RuntimeError(error_msg) from e
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(
                f"Successfully loaded {row_count} rows into silver.{table_name}",
                metadata={
                    'table_name': table_name,
                    'row_count': row_count,
                    'execution_time_seconds': execution_time,
                    'attempt': attempt
                }
            )
            return row_count
        
        except RuntimeError:
            if attempt >= max_retries:
                raise
        except Exception as e:
            error_msg = f"Unexpected error loading {parquet_file}: {str(e)}"
            logger.error(error_msg, metadata={'parquet_file': str(parquet_file), 'error': str(e), 'traceback': traceback.format_exc()})
            
            if attempt < max_retries:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                raise RuntimeError(error_msg) from e
    
    # Should not reach here
    raise RuntimeError(f"Failed to load {parquet_file} after {max_retries} attempts")


def main():
    """Main function to load all Silver layer Parquet files."""
    # Get Silver data path
    silver_path = os.getenv('SILVER_DATA_PATH', 'data/silver')
    
    # Get run date (default to today)
    run_date = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime('%Y-%m-%d')
    
    silver_dir = Path(silver_path) / run_date
    
    if not silver_dir.exists():
        logger.error(f"Silver directory not found: {silver_dir}")
        sys.exit(1)
    
    logger.info(f"Loading Silver layer data from {silver_dir}")
    
    # Create database connection
    connection_string = get_db_connection_string()
    engine = create_engine(connection_string)
    
    # Create staging schema
    create_staging_schema(engine)
    
    # Define tables to load
    tables = [
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
    
    # Load each table
    total_rows = 0
    for table in tables:
        parquet_file = silver_dir / f"{table}.parquet"
        
        if not parquet_file.exists():
            logger.warning(f"Parquet file not found: {parquet_file}")
            continue
        
        try:
            rows = load_parquet_to_postgres(parquet_file, table, engine)
            total_rows += rows
        except Exception as e:
            logger.error(f"Failed to load {table}: {str(e)}")
            # Continue with other tables
    
    logger.info(f"Completed loading {total_rows} total rows from {len(tables)} tables")
    
    # Close engine
    engine.dispose()


if __name__ == '__main__':
    main()
