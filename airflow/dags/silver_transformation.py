"""
Silver Layer Transformation Module

This module handles the transformation of Bronze layer CSV files into cleaned,
validated Silver layer Parquet files with standardized formats and audit columns.
"""

import os
import hashlib
import pandas as pd
import yaml
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

# Import centralized logger
from logger import get_logger

# Configure logging
logger = get_logger(__name__)


class SilverTransformationError(Exception):
    """Custom exception for Silver layer transformation errors"""
    pass


def standardize_date(
    date_value: Any,
    source_format: str = "%d-%m-%Y",
    target_format: str = "%Y-%m-%d"
) -> Optional[str]:
    """
    Standardize date from DD-MM-YYYY to YYYY-MM-DD format.
    
    Args:
        date_value: Date value to standardize (string or other type)
        source_format: Source date format (default: DD-MM-YYYY)
        target_format: Target date format (default: YYYY-MM-DD)
    
    Returns:
        Standardized date string in target format, or None if invalid
    """
    if pd.isna(date_value) or date_value == '' or date_value is None:
        return None
    
    try:
        # Convert to string if not already
        date_str = str(date_value).strip()
        
        # Handle dates with timestamps (e.g., "22-03-2025 00:00")
        # Split on space and take only the date part
        if ' ' in date_str:
            date_str = date_str.split(' ')[0]
        
        # Parse with source format
        date_obj = datetime.strptime(date_str, source_format)
        
        # Return in target format
        return date_obj.strftime(target_format)
    
    except (ValueError, TypeError) as e:
        logger.warning(f"Failed to parse date '{date_value}': {str(e)}")
        return None


def convert_to_string(value: Any) -> Optional[str]:
    """
    Convert value to string type, handling nulls appropriately.
    
    Args:
        value: Value to convert
    
    Returns:
        String value or None if null/empty
    """
    if pd.isna(value) or value == '' or value is None:
        return None
    return str(value).strip()


def convert_to_integer(value: Any) -> Optional[int]:
    """
    Convert value to integer type, handling nulls and invalid values.
    
    Args:
        value: Value to convert
    
    Returns:
        Integer value or None if null/invalid
    """
    if pd.isna(value) or value == '' or value is None:
        return None
    
    try:
        # Handle string representations
        if isinstance(value, str):
            value = value.strip()
            if value == '':
                return None
        
        return int(float(value))
    
    except (ValueError, TypeError) as e:
        logger.warning(f"Failed to convert '{value}' to integer: {str(e)}")
        return None


def convert_to_float(value: Any, decimal_places: int = 2) -> Optional[float]:
    """
    Convert value to float type with specified decimal places.
    
    Args:
        value: Value to convert
        decimal_places: Number of decimal places to round to
    
    Returns:
        Float value or None if null/invalid
    """
    if pd.isna(value) or value == '' or value is None:
        return None
    
    try:
        # Handle string representations
        if isinstance(value, str):
            value = value.strip()
            if value == '':
                return None
        
        float_val = float(value)
        return round(float_val, decimal_places)
    
    except (ValueError, TypeError) as e:
        logger.warning(f"Failed to convert '{value}' to float: {str(e)}")
        return None


def handle_missing_data(
    df: pd.DataFrame,
    column: str,
    strategy: str,
    fill_value: Any = None
) -> pd.DataFrame:
    """
    Handle missing data in a DataFrame column using specified strategy.
    
    Args:
        df: DataFrame to process
        column: Column name to handle
        strategy: Strategy to use ('fill', 'keep_null', 'drop')
        fill_value: Value to fill with if strategy is 'fill'
    
    Returns:
        DataFrame with missing data handled
    """
    if column not in df.columns:
        logger.warning(f"Column '{column}' not found in DataFrame")
        return df
    
    if strategy == 'fill':
        if fill_value is not None:
            df[column] = df[column].fillna(fill_value)
            logger.debug(f"Filled missing values in '{column}' with '{fill_value}'")
    
    elif strategy == 'keep_null':
        # Keep nulls as-is (no action needed)
        pass
    
    elif strategy == 'drop':
        original_count = len(df)
        df = df.dropna(subset=[column])
        dropped_count = original_count - len(df)
        if dropped_count > 0:
            logger.info(f"Dropped {dropped_count} rows with null values in '{column}'")
    
    else:
        logger.warning(f"Unknown missing data strategy: {strategy}")
    
    return df


def deduplicate_records(
    df: pd.DataFrame,
    primary_keys: List[str],
    keep: str = 'first'
) -> pd.DataFrame:
    """
    Remove duplicate records based on primary key fields.
    
    Args:
        df: DataFrame to deduplicate
        primary_keys: List of column names that form the primary key
        keep: Which duplicate to keep ('first', 'last', False to drop all)
    
    Returns:
        Deduplicated DataFrame
    """
    if not primary_keys:
        logger.warning("No primary keys specified for deduplication")
        return df
    
    # Check if all primary key columns exist
    missing_keys = [key for key in primary_keys if key not in df.columns]
    if missing_keys:
        logger.warning(f"Primary key columns not found: {missing_keys}")
        return df
    
    original_count = len(df)
    df = df.drop_duplicates(subset=primary_keys, keep=keep)
    duplicates_removed = original_count - len(df)
    
    if duplicates_removed > 0:
        logger.info(
            f"Removed {duplicates_removed} duplicate records based on "
            f"primary keys: {', '.join(primary_keys)}"
        )
    
    return df


def calculate_record_hash(row: pd.Series) -> str:
    """
    Calculate MD5 hash for a record (row) for change detection.
    
    Args:
        row: Pandas Series representing a row
    
    Returns:
        MD5 hash string
    """
    # Convert row to string representation
    row_str = '|'.join(str(val) for val in row.values)
    
    # Calculate MD5 hash
    hash_obj = hashlib.md5(row_str.encode('utf-8'))
    return hash_obj.hexdigest()


def add_audit_columns(
    df: pd.DataFrame,
    source_file: str,
    load_timestamp: Optional[datetime] = None
) -> pd.DataFrame:
    """
    Add audit columns to DataFrame for tracking and lineage.
    
    Args:
        df: DataFrame to add audit columns to
        source_file: Name of the source file
        load_timestamp: Timestamp of the load (defaults to current UTC time)
    
    Returns:
        DataFrame with audit columns added
    """
    if load_timestamp is None:
        load_timestamp = datetime.now(timezone.utc)
    
    # Add load timestamp
    df['load_timestamp'] = load_timestamp.isoformat()
    
    # Add source file
    df['source_file'] = source_file
    
    # Calculate record hash for each row
    df['record_hash'] = df.apply(
        lambda row: calculate_record_hash(row.drop(['load_timestamp', 'source_file'])),
        axis=1
    )
    
    logger.info(f"Added audit columns: load_timestamp, source_file, record_hash")
    
    return df


def apply_date_transformations(
    df: pd.DataFrame,
    date_columns: List[str],
    source_format: str = "%d-%m-%Y"
) -> pd.DataFrame:
    """
    Apply date standardization to specified columns.
    
    Args:
        df: DataFrame to transform
        date_columns: List of column names containing dates
        source_format: Source date format
    
    Returns:
        DataFrame with standardized dates
    """
    for col in date_columns:
        if col in df.columns:
            logger.debug(f"Standardizing dates in column: {col}")
            df[col] = df[col].apply(lambda x: standardize_date(x, source_format))
    
    return df


def apply_type_conversions(
    df: pd.DataFrame,
    type_config: Dict[str, str]
) -> pd.DataFrame:
    """
    Apply data type conversions based on configuration.
    
    Args:
        df: DataFrame to transform
        type_config: Dictionary mapping column names to target types
                    ('string', 'integer', 'float', 'date')
    
    Returns:
        DataFrame with converted types
    """
    for col, target_type in type_config.items():
        if col not in df.columns:
            continue
        
        logger.debug(f"Converting column '{col}' to type: {target_type}")
        
        if target_type == 'string':
            df[col] = df[col].apply(convert_to_string)
        
        elif target_type == 'integer':
            df[col] = df[col].apply(convert_to_integer)
        
        elif target_type == 'float':
            df[col] = df[col].apply(convert_to_float)
        
        elif target_type == 'date':
            # Dates are handled separately in apply_date_transformations
            pass
        
        else:
            logger.warning(f"Unknown target type '{target_type}' for column '{col}'")
    
    return df


def apply_missing_data_strategies(
    df: pd.DataFrame,
    missing_data_config: Dict[str, Dict[str, Any]]
) -> pd.DataFrame:
    """
    Apply missing data handling strategies based on configuration.
    
    Args:
        df: DataFrame to transform
        missing_data_config: Dictionary mapping column names to strategy configs
                           e.g., {'phone': {'strategy': 'fill', 'value': 'NOT_PROVIDED'}}
    
    Returns:
        DataFrame with missing data handled
    """
    for col, config in missing_data_config.items():
        if col not in df.columns:
            continue
        
        strategy = config.get('strategy', 'keep_null')
        fill_value = config.get('value')
        
        df = handle_missing_data(df, col, strategy, fill_value)
    
    return df


def transform_table(
    bronze_file: str,
    table_config: Dict[str, Any],
    source_file_name: str
) -> pd.DataFrame:
    """
    Main transformation function to clean and transform Bronze data to Silver.
    
    This function applies the following transformations:
    1. Load CSV from Bronze layer
    2. Standardize date formats
    3. Convert data types
    4. Handle missing data
    5. Remove duplicates
    6. Add audit columns
    
    Args:
        bronze_file: Path to Bronze layer CSV file
        table_config: Configuration dictionary for the table
        source_file_name: Original source file name for audit trail
    
    Returns:
        Transformed DataFrame ready for Silver layer
    
    Raises:
        SilverTransformationError: If transformation fails
    """
    start_time = datetime.now(timezone.utc)
    
    try:
        logger.info(
            f"Starting transformation for: {bronze_file}",
            metadata={'bronze_file': bronze_file, 'source_file': source_file_name}
        )
        
        # Load CSV file
        try:
            df = pd.read_csv(bronze_file, low_memory=False)
            original_row_count = len(df)
            original_columns = list(df.columns)
            logger.info(
                f"Loaded {original_row_count} rows from Bronze layer",
                metadata={'row_count': original_row_count, 'columns': len(original_columns)}
            )
            
            # Log data sample for debugging
            if original_row_count > 0:
                sample_data = df.head(3).to_dict('records')
                logger.debug(
                    "Data sample loaded",
                    metadata={'sample_rows': sample_data, 'columns': original_columns}
                )
        
        except FileNotFoundError as e:
            error_msg = f"Bronze file not found: {bronze_file}"
            logger.error(error_msg, metadata={'bronze_file': bronze_file, 'error': str(e)})
            raise SilverTransformationError(error_msg) from e
        
        except pd.errors.EmptyDataError as e:
            error_msg = f"Bronze file is empty: {bronze_file}"
            logger.error(error_msg, metadata={'bronze_file': bronze_file, 'error': str(e)})
            raise SilverTransformationError(error_msg) from e
        
        except Exception as e:
            error_msg = f"Failed to load Bronze file {bronze_file}: {str(e)}"
            logger.error(error_msg, metadata={'bronze_file': bronze_file, 'error': str(e), 'traceback': traceback.format_exc()})
            raise SilverTransformationError(error_msg) from e
        
        # Apply date transformations
        date_columns = table_config.get('date_columns', [])
        if date_columns:
            try:
                df = apply_date_transformations(df, date_columns)
                logger.debug(f"Applied date transformations to {len(date_columns)} columns")
            except Exception as e:
                error_msg = f"Date transformation failed: {str(e)}"
                logger.error(error_msg, metadata={'date_columns': date_columns, 'error': str(e)})
                raise SilverTransformationError(error_msg) from e
        
        # Apply type conversions
        type_config = table_config.get('type_conversions', {})
        if type_config:
            try:
                df = apply_type_conversions(df, type_config)
                logger.debug(f"Applied type conversions to {len(type_config)} columns")
            except Exception as e:
                error_msg = f"Type conversion failed: {str(e)}"
                logger.error(error_msg, metadata={'type_config': type_config, 'error': str(e)})
                raise SilverTransformationError(error_msg) from e
        
        # Handle missing data
        missing_data_config = table_config.get('missing_data', {})
        if missing_data_config:
            try:
                df = apply_missing_data_strategies(df, missing_data_config)
                logger.debug(f"Applied missing data strategies to {len(missing_data_config)} columns")
            except Exception as e:
                error_msg = f"Missing data handling failed: {str(e)}"
                logger.error(error_msg, metadata={'missing_data_config': missing_data_config, 'error': str(e)})
                raise SilverTransformationError(error_msg) from e
        
        # Deduplicate records
        primary_keys = table_config.get('primary_keys', [])
        if primary_keys:
            try:
                df = deduplicate_records(df, primary_keys)
            except Exception as e:
                error_msg = f"Deduplication failed: {str(e)}"
                logger.error(error_msg, metadata={'primary_keys': primary_keys, 'error': str(e)})
                raise SilverTransformationError(error_msg) from e
        
        # Add audit columns
        try:
            df = add_audit_columns(df, source_file_name)
        except Exception as e:
            error_msg = f"Failed to add audit columns: {str(e)}"
            logger.error(error_msg, metadata={'source_file': source_file_name, 'error': str(e)})
            raise SilverTransformationError(error_msg) from e
        
        final_row_count = len(df)
        execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        
        logger.info(
            f"Transformation complete: {original_row_count} -> {final_row_count} rows "
            f"({original_row_count - final_row_count} removed)",
            metadata={
                'original_rows': original_row_count,
                'final_rows': final_row_count,
                'rows_removed': original_row_count - final_row_count,
                'execution_time_seconds': execution_time
            }
        )
        
        return df
    
    except SilverTransformationError:
        raise
    except Exception as e:
        error_msg = f"Unexpected error transforming {bronze_file}: {str(e)}"
        logger.critical(
            error_msg,
            metadata={'bronze_file': bronze_file, 'error_type': type(e).__name__, 'error': str(e), 'traceback': traceback.format_exc()}
        )
        raise SilverTransformationError(error_msg) from e


def write_to_parquet(
    df: pd.DataFrame,
    silver_dir: str,
    table_name: str,
    run_date: str,
    compression: str = 'snappy'
) -> str:
    """
    Write DataFrame to Parquet format with compression in Silver layer.
    
    Args:
        df: DataFrame to write
        silver_dir: Base Silver layer directory
        table_name: Name of the table (without .csv extension)
        run_date: Run date in YYYY-MM-DD format
        compression: Compression algorithm ('snappy', 'gzip', 'brotli', 'none')
    
    Returns:
        Path to the written Parquet file
    
    Raises:
        SilverTransformationError: If writing fails
    """
    try:
        # Create Silver directory structure by date
        silver_path = Path(silver_dir) / run_date
        silver_path.mkdir(parents=True, exist_ok=True)
        
        # Create Parquet filename
        parquet_filename = f"{table_name}.parquet"
        parquet_path = silver_path / parquet_filename
        
        logger.info(f"Writing {len(df)} rows to Parquet: {parquet_path}")
        
        # Write to Parquet with compression
        df.to_parquet(
            parquet_path,
            engine='pyarrow',
            compression=compression,
            index=False
        )
        
        # Get file size for logging
        file_size = os.path.getsize(parquet_path)
        logger.info(
            f"Successfully wrote Parquet file: {parquet_filename} "
            f"({file_size / 1024 / 1024:.2f} MB, compression: {compression})"
        )
        
        return str(parquet_path)
    
    except Exception as e:
        logger.error(f"Failed to write Parquet file: {str(e)}")
        raise SilverTransformationError(f"Failed to write Parquet: {str(e)}") from e


def load_table_config(config_file: str) -> Dict[str, Any]:
    """
    Load table transformation configuration from YAML file.
    
    Args:
        config_file: Path to YAML configuration file
    
    Returns:
        Dictionary containing table configurations
    
    Raises:
        SilverTransformationError: If config file cannot be loaded
    """
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        logger.info(f"Loaded configuration for {len(config)} tables")
        return config
    
    except Exception as e:
        logger.error(f"Failed to load configuration file: {str(e)}")
        raise SilverTransformationError(f"Failed to load config: {str(e)}") from e


def transform_bronze_to_silver(
    bronze_dir: str,
    silver_dir: str,
    config_file: str,
    run_date: str,
    table_name: Optional[str] = None
) -> Dict[str, str]:
    """
    Transform Bronze layer CSV files to Silver layer Parquet files.
    
    This is the main orchestration function that:
    1. Loads table configurations
    2. Finds Bronze layer files for the run date
    3. Transforms each table
    4. Writes to Parquet in Silver layer
    
    Args:
        bronze_dir: Base Bronze layer directory
        silver_dir: Base Silver layer directory
        config_file: Path to table configuration YAML file
        run_date: Run date in YYYY-MM-DD format
        table_name: Optional specific table to transform (transforms all if None)
    
    Returns:
        Dictionary mapping table names to Silver Parquet file paths
    
    Raises:
        SilverTransformationError: If transformation fails
    """
    try:
        logger.info(f"Starting Bronze to Silver transformation for run date: {run_date}")
        
        # Load table configurations
        table_configs = load_table_config(config_file)
        
        # Determine which tables to process
        if table_name:
            if table_name not in table_configs:
                raise SilverTransformationError(f"Table '{table_name}' not found in config")
            tables_to_process = {table_name: table_configs[table_name]}
        else:
            tables_to_process = table_configs
        
        # Find Bronze directory for run date
        bronze_run_dir = Path(bronze_dir) / run_date
        if not bronze_run_dir.exists():
            raise SilverTransformationError(
                f"Bronze directory not found for run date {run_date}: {bronze_run_dir}"
            )
        
        # Process each table
        results = {}
        
        for table, config in tables_to_process.items():
            logger.info(f"Processing table: {table}")
            
            # Find Bronze CSV file (with timestamp prefix)
            bronze_file = bronze_run_dir / f"{run_date}_{table}.csv"
            
            if not bronze_file.exists():
                logger.warning(f"Bronze file not found: {bronze_file}")
                continue
            
            # Transform table
            transformed_df = transform_table(
                str(bronze_file),
                config,
                f"{table}.csv"
            )
            
            # Write to Parquet
            parquet_path = write_to_parquet(
                transformed_df,
                silver_dir,
                table,
                run_date
            )
            
            results[table] = parquet_path
            logger.info(f"Completed transformation for table: {table}")
        
        logger.info(
            f"Silver layer transformation complete. "
            f"Processed {len(results)} tables."
        )
        
        return results
    
    except SilverTransformationError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during transformation: {str(e)}")
        raise SilverTransformationError(f"Transformation failed: {str(e)}") from e


if __name__ == '__main__':
    """
    Command-line interface for Silver layer transformation.
    
    Usage:
        python silver_transformation.py [table_name]
        
    Environment variables:
        BRONZE_DATA_PATH: Bronze directory (default: ./data/bronze)
        SILVER_DATA_PATH: Silver directory (default: ./data/silver)
        SILVER_CONFIG_PATH: Config file (default: ./config/silver_table_config.yaml)
    """
    import sys
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Get paths from environment or use defaults
    bronze_path = os.getenv('BRONZE_DATA_PATH', './data/bronze')
    silver_path = os.getenv('SILVER_DATA_PATH', './data/silver')
    config_path = os.getenv('SILVER_CONFIG_PATH', './config/silver_table_config.yaml')
    
    # Get run date (default to today)
    run_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    
    # Get optional table name from command line
    table_name = sys.argv[1] if len(sys.argv) > 1 else None
    
    try:
        results = transform_bronze_to_silver(
            bronze_path,
            silver_path,
            config_path,
            run_date,
            table_name
        )
        
        print("\n" + "="*60)
        print("SILVER LAYER TRANSFORMATION SUMMARY")
        print("="*60)
        print(f"Run Date: {run_date}")
        print(f"Tables Processed: {len(results)}")
        print("="*60)
        for table, parquet_path in results.items():
            print(f"  {table:<30} -> {Path(parquet_path).name}")
        print("="*60 + "\n")
        
        sys.exit(0)
        
    except SilverTransformationError as e:
        print(f"\nERROR: {str(e)}\n", file=sys.stderr)
        sys.exit(1)
