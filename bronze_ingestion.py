"""
Bronze Layer Ingestion Module

This module handles the ingestion of raw CSV files into the Bronze layer,
maintaining immutability and generating metadata for data lineage.
"""

import os
import shutil
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
import traceback

# Import centralized logger
from logger import get_logger

# Configure logging
logger = get_logger(__name__)

# Expected CSV files based on requirements
EXPECTED_CSV_FILES = [
    'patients.csv',
    'encounters.csv',
    'diagnoses.csv',
    'procedures.csv',
    'medications.csv',
    'lab_tests.csv',
    'claims_and_billing.csv',
    'providers.csv',
    'denials.csv'
]


class BronzeIngestionError(Exception):
    """Custom exception for Bronze layer ingestion errors"""
    pass


def calculate_file_checksum(file_path: str, algorithm: str = 'md5') -> str:
    """
    Calculate checksum for a file.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use (default: md5)
    
    Returns:
        Hexadecimal checksum string
    
    Raises:
        BronzeIngestionError: If checksum calculation fails
    """
    try:
        hash_func = hashlib.new(algorithm)
        
        with open(file_path, 'rb') as f:
            # Read file in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(8192), b''):
                hash_func.update(chunk)
        
        return hash_func.hexdigest()
    
    except FileNotFoundError as e:
        error_msg = f"File not found for checksum calculation: {file_path}"
        logger.error(error_msg, metadata={'file_path': file_path, 'error': str(e)})
        raise BronzeIngestionError(error_msg) from e
    
    except PermissionError as e:
        error_msg = f"Permission denied reading file: {file_path}"
        logger.error(error_msg, metadata={'file_path': file_path, 'error': str(e)})
        raise BronzeIngestionError(error_msg) from e
    
    except Exception as e:
        error_msg = f"Failed to calculate checksum for {file_path}: {str(e)}"
        logger.error(error_msg, metadata={'file_path': file_path, 'error': str(e), 'traceback': traceback.format_exc()})
        raise BronzeIngestionError(error_msg) from e


def count_csv_rows(file_path: str) -> int:
    """
    Count the number of rows in a CSV file (excluding header).
    
    Args:
        file_path: Path to the CSV file
    
    Returns:
        Number of data rows (excluding header)
    
    Raises:
        BronzeIngestionError: If row counting fails
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Subtract 1 for header row
            row_count = sum(1 for _ in f) - 1
        
        return max(0, row_count)  # Ensure non-negative
    
    except FileNotFoundError as e:
        error_msg = f"File not found for row counting: {file_path}"
        logger.error(error_msg, metadata={'file_path': file_path, 'error': str(e)})
        raise BronzeIngestionError(error_msg) from e
    
    except UnicodeDecodeError as e:
        error_msg = f"Invalid file encoding for {file_path}: {str(e)}"
        logger.error(error_msg, metadata={'file_path': file_path, 'error': str(e)})
        raise BronzeIngestionError(error_msg) from e
    
    except Exception as e:
        error_msg = f"Failed to count rows in {file_path}: {str(e)}"
        logger.error(error_msg, metadata={'file_path': file_path, 'error': str(e), 'traceback': traceback.format_exc()})
        raise BronzeIngestionError(error_msg) from e


def get_file_size(file_path: str) -> int:
    """
    Get file size in bytes.
    
    Args:
        file_path: Path to the file
    
    Returns:
        File size in bytes
    """
    return os.path.getsize(file_path)


def validate_csv_files(source_dir: str) -> List[str]:
    """
    Validate that all expected CSV files are present in the source directory.
    
    Args:
        source_dir: Directory containing source CSV files
    
    Returns:
        List of validated file paths
    
    Raises:
        BronzeIngestionError: If any expected files are missing
    """
    source_path = Path(source_dir)
    
    if not source_path.exists():
        raise BronzeIngestionError(f"Source directory does not exist: {source_dir}")
    
    if not source_path.is_dir():
        raise BronzeIngestionError(f"Source path is not a directory: {source_dir}")
    
    missing_files = []
    found_files = []
    
    for csv_file in EXPECTED_CSV_FILES:
        file_path = source_path / csv_file
        if file_path.exists() and file_path.is_file():
            found_files.append(str(file_path))
            logger.info(f"Found CSV file: {csv_file}")
        else:
            missing_files.append(csv_file)
            logger.error(f"Missing CSV file: {csv_file}")
    
    if missing_files:
        raise BronzeIngestionError(
            f"Missing {len(missing_files)} required CSV file(s): {', '.join(missing_files)}"
        )
    
    logger.info(f"All {len(EXPECTED_CSV_FILES)} expected CSV files validated successfully")
    return found_files


def create_bronze_directory(bronze_dir: str, run_date: str) -> Path:
    """
    Create Bronze layer directory structure for the given run date.
    
    Args:
        bronze_dir: Base Bronze layer directory
        run_date: Run date in YYYY-MM-DD format
    
    Returns:
        Path object for the created directory
    """
    bronze_path = Path(bronze_dir) / run_date
    bronze_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created Bronze directory: {bronze_path}")
    return bronze_path


def copy_csv_to_bronze(
    source_file: str,
    bronze_dir: Path,
    run_date: str
) -> Dict[str, any]:
    """
    Copy a CSV file to the Bronze layer with timestamp prefix.
    
    Args:
        source_file: Path to source CSV file
        bronze_dir: Bronze layer directory for this run
        run_date: Run date in YYYY-MM-DD format
    
    Returns:
        Dictionary with file metadata
    
    Raises:
        BronzeIngestionError: If file copy or metadata generation fails
    """
    try:
        source_path = Path(source_file)
        filename = source_path.name
        
        # Create timestamped filename
        timestamped_filename = f"{run_date}_{filename}"
        destination_path = bronze_dir / timestamped_filename
        
        # Copy file
        logger.info(f"Copying {filename} to Bronze layer...", metadata={'source': source_file, 'destination': str(destination_path)})
        
        try:
            shutil.copy2(source_file, destination_path)
        except PermissionError as e:
            error_msg = f"Permission denied copying file {filename}"
            logger.error(error_msg, metadata={'source': source_file, 'destination': str(destination_path), 'error': str(e)})
            raise BronzeIngestionError(error_msg) from e
        except OSError as e:
            error_msg = f"OS error copying file {filename}: {str(e)}"
            logger.error(error_msg, metadata={'source': source_file, 'destination': str(destination_path), 'error': str(e)})
            raise BronzeIngestionError(error_msg) from e
        
        # Generate metadata
        try:
            row_count = count_csv_rows(str(destination_path))
            file_size = get_file_size(str(destination_path))
            checksum = calculate_file_checksum(str(destination_path))
        except Exception as e:
            # Clean up copied file if metadata generation fails
            if destination_path.exists():
                destination_path.unlink()
            error_msg = f"Failed to generate metadata for {filename}"
            logger.error(error_msg, metadata={'file': filename, 'error': str(e)})
            raise BronzeIngestionError(error_msg) from e
        
        metadata = {
            'source_file': filename,
            'bronze_file': timestamped_filename,
            'row_count': row_count,
            'file_size_bytes': file_size,
            'checksum_md5': checksum,
            'ingestion_timestamp': datetime.now(timezone.utc).isoformat(),
            'run_date': run_date
        }
        
        logger.info(
            f"Copied {filename}: {row_count} rows, "
            f"{file_size / 1024 / 1024:.2f} MB, checksum: {checksum[:8]}...",
            metadata={'row_count': row_count, 'file_size_mb': file_size / 1024 / 1024, 'checksum': checksum}
        )
        
        return metadata
    
    except BronzeIngestionError:
        raise
    except Exception as e:
        error_msg = f"Unexpected error copying {source_file} to Bronze layer: {str(e)}"
        logger.error(error_msg, metadata={'source_file': source_file, 'error': str(e), 'traceback': traceback.format_exc()})
        raise BronzeIngestionError(error_msg) from e


def generate_metadata_file(
    bronze_dir: Path,
    files_metadata: List[Dict],
    run_date: str
) -> str:
    """
    Generate a metadata JSON file for the Bronze layer ingestion.
    
    Args:
        bronze_dir: Bronze layer directory for this run
        files_metadata: List of metadata dictionaries for each file
        run_date: Run date in YYYY-MM-DD format
    
    Returns:
        Path to the generated metadata file
    """
    metadata_file = bronze_dir / '_metadata.json'
    
    # Calculate totals
    total_rows = sum(f['row_count'] for f in files_metadata)
    total_size = sum(f['file_size_bytes'] for f in files_metadata)
    
    metadata = {
        'run_date': run_date,
        'ingestion_timestamp': datetime.now(timezone.utc).isoformat(),
        'total_files': len(files_metadata),
        'total_rows': total_rows,
        'total_size_bytes': total_size,
        'files': files_metadata
    }
    
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Generated metadata file: {metadata_file}")
    logger.info(
        f"Summary: {len(files_metadata)} files, {total_rows:,} total rows, "
        f"{total_size / 1024 / 1024:.2f} MB"
    )
    
    return str(metadata_file)


def ingest_csv_files(
    source_dir: str,
    bronze_dir: str,
    run_date: Optional[str] = None
) -> Dict[str, int]:
    """
    Main function to ingest CSV files into the Bronze layer.
    
    This function:
    1. Validates all expected CSV files are present
    2. Creates Bronze directory structure with run date
    3. Copies each CSV file with timestamp prefix
    4. Generates metadata file with row counts, file sizes, and checksums
    
    Args:
        source_dir: Directory containing source CSV files
        bronze_dir: Base Bronze layer directory
        run_date: Run date in YYYY-MM-DD format (defaults to today)
    
    Returns:
        Dictionary mapping filename to row count
    
    Raises:
        BronzeIngestionError: If validation fails or ingestion encounters errors
    
    Example:
        >>> result = ingest_csv_files(
        ...     source_dir='./dataset',
        ...     bronze_dir='./data/bronze',
        ...     run_date='2025-01-15'
        ... )
        >>> print(result)
        {'patients.csv': 10000, 'encounters.csv': 15000, ...}
    """
    start_time = datetime.now(timezone.utc)
    
    try:
        # Use current date if not provided
        if run_date is None:
            run_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        
        logger.info(
            f"Starting Bronze layer ingestion for run date: {run_date}",
            metadata={'source_dir': source_dir, 'bronze_dir': bronze_dir, 'run_date': run_date}
        )
        
        # Step 1: Validate all expected CSV files are present
        try:
            validated_files = validate_csv_files(source_dir)
        except BronzeIngestionError as e:
            logger.error(
                f"File validation failed: {str(e)}",
                metadata={'source_dir': source_dir, 'expected_files': EXPECTED_CSV_FILES}
            )
            raise
        
        # Step 2: Create Bronze directory structure
        try:
            bronze_run_dir = create_bronze_directory(bronze_dir, run_date)
        except Exception as e:
            error_msg = f"Failed to create Bronze directory: {str(e)}"
            logger.error(error_msg, metadata={'bronze_dir': bronze_dir, 'run_date': run_date, 'error': str(e)})
            raise BronzeIngestionError(error_msg) from e
        
        # Step 3: Copy each CSV file and collect metadata
        files_metadata = []
        row_counts = {}
        failed_files = []
        
        for source_file in validated_files:
            try:
                file_metadata = copy_csv_to_bronze(source_file, bronze_run_dir, run_date)
                files_metadata.append(file_metadata)
                row_counts[file_metadata['source_file']] = file_metadata['row_count']
            except BronzeIngestionError as e:
                failed_files.append({'file': source_file, 'error': str(e)})
                logger.error(
                    f"Failed to copy file {source_file}: {str(e)}",
                    metadata={'source_file': source_file, 'error': str(e)}
                )
        
        # Check if any files failed
        if failed_files:
            error_msg = f"Failed to copy {len(failed_files)} file(s)"
            logger.error(error_msg, metadata={'failed_files': failed_files})
            raise BronzeIngestionError(f"{error_msg}: {[f['file'] for f in failed_files]}")
        
        # Step 4: Generate metadata file
        try:
            metadata_file = generate_metadata_file(bronze_run_dir, files_metadata, run_date)
        except Exception as e:
            error_msg = f"Failed to generate metadata file: {str(e)}"
            logger.error(error_msg, metadata={'bronze_dir': str(bronze_run_dir), 'error': str(e)})
            raise BronzeIngestionError(error_msg) from e
        
        # Calculate execution time
        end_time = datetime.now(timezone.utc)
        execution_time = (end_time - start_time).total_seconds()
        
        logger.info(
            "Bronze layer ingestion completed successfully",
            metadata={
                'metadata_file': metadata_file,
                'files_processed': len(files_metadata),
                'total_rows': sum(row_counts.values()),
                'execution_time_seconds': execution_time
            }
        )
        
        return row_counts
        
    except BronzeIngestionError as e:
        logger.error(
            f"Bronze ingestion failed: {str(e)}",
            metadata={'error_type': 'BronzeIngestionError', 'error': str(e)}
        )
        raise
    except Exception as e:
        error_msg = f"Unexpected error during Bronze ingestion: {str(e)}"
        logger.critical(
            error_msg,
            metadata={'error_type': type(e).__name__, 'error': str(e), 'traceback': traceback.format_exc()}
        )
        raise BronzeIngestionError(error_msg) from e


if __name__ == '__main__':
    """
    Command-line interface for Bronze layer ingestion.
    
    Usage:
        python bronze_ingestion.py
        
    Environment variables:
        SOURCE_CSV_PATH: Source directory (default: ./dataset)
        BRONZE_DATA_PATH: Bronze directory (default: ./data/bronze)
    """
    import sys
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Get paths from environment or use defaults
    source_path = os.getenv('SOURCE_CSV_PATH', './dataset')
    bronze_path = os.getenv('BRONZE_DATA_PATH', './data/bronze')
    
    try:
        result = ingest_csv_files(source_path, bronze_path)
        
        print("\n" + "="*60)
        print("BRONZE LAYER INGESTION SUMMARY")
        print("="*60)
        for filename, row_count in result.items():
            print(f"  {filename:<30} {row_count:>10,} rows")
        print("="*60)
        print(f"Total files ingested: {len(result)}")
        print("="*60 + "\n")
        
        sys.exit(0)
        
    except BronzeIngestionError as e:
        print(f"\nERROR: {str(e)}\n", file=sys.stderr)
        sys.exit(1)
