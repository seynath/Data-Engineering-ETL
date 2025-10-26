"""
Centralized Logging Module

This module provides structured JSON logging configuration for the healthcare ETL pipeline.
It implements consistent logging across all pipeline components with proper formatting,
log levels, file rotation, and retention policies.
"""

import os
import sys
import json
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from pythonjsonlogger import jsonlogger


# Default log configuration
DEFAULT_LOG_DIR = "logs"
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FILE = "pipeline.log"
DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
DEFAULT_BACKUP_COUNT = 10  # Keep 10 backup files
DEFAULT_RETENTION_DAYS = 30


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter that adds additional context fields to log records
    """
    
    def add_fields(self, log_record: Dict, record: logging.LogRecord, message_dict: Dict):
        """
        Add custom fields to the log record
        
        Args:
            log_record: Dictionary to be logged as JSON
            record: Original LogRecord object
            message_dict: Dictionary from the log message
        """
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        
        # Add timestamp in ISO format
        if not log_record.get('timestamp'):
            from datetime import timezone
            log_record['timestamp'] = datetime.now(timezone.utc).isoformat()
        
        # Add log level
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname
        
        # Add logger name
        log_record['logger'] = record.name
        
        # Add module and function information
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno
        
        # Add process and thread information
        log_record['process_id'] = record.process
        log_record['thread_id'] = record.thread
        
        # Add any extra fields from the record
        if hasattr(record, 'task_id'):
            log_record['task_id'] = record.task_id
        
        if hasattr(record, 'dag_id'):
            log_record['dag_id'] = record.dag_id
        
        if hasattr(record, 'run_id'):
            log_record['run_id'] = record.run_id
        
        if hasattr(record, 'metadata'):
            log_record['metadata'] = record.metadata


class PipelineLogger:
    """
    Centralized logger for the healthcare ETL pipeline
    """
    
    def __init__(
        self,
        name: str,
        log_dir: Optional[str] = None,
        log_level: Optional[str] = None,
        log_file: Optional[str] = None,
        enable_console: bool = True,
        enable_file: bool = True,
        enable_json: bool = True,
        max_bytes: Optional[int] = None,
        backup_count: Optional[int] = None
    ):
        """
        Initialize the pipeline logger
        
        Args:
            name: Logger name (typically module name)
            log_dir: Directory for log files
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Log file name
            enable_console: Enable console logging
            enable_file: Enable file logging
            enable_json: Use JSON formatting for file logs
            max_bytes: Maximum size of log file before rotation
            backup_count: Number of backup files to keep
        """
        self.name = name
        self.log_dir = log_dir or os.getenv('LOG_DIR', DEFAULT_LOG_DIR)
        self.log_level = log_level or os.getenv('LOG_LEVEL', DEFAULT_LOG_LEVEL)
        self.log_file = log_file or os.getenv('LOG_FILE', DEFAULT_LOG_FILE)
        self.enable_console = enable_console
        self.enable_file = enable_file
        self.enable_json = enable_json
        self.max_bytes = max_bytes or DEFAULT_MAX_BYTES
        self.backup_count = backup_count or DEFAULT_BACKUP_COUNT
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self._get_log_level(self.log_level))
        
        # Remove existing handlers to avoid duplicates
        self.logger.handlers = []
        
        # Add handlers
        if self.enable_console:
            self._add_console_handler()
        
        if self.enable_file:
            self._add_file_handler()
    
    def _get_log_level(self, level_str: str) -> int:
        """
        Convert log level string to logging constant
        
        Args:
            level_str: Log level as string
            
        Returns:
            Logging level constant
        """
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        return level_map.get(level_str.upper(), logging.INFO)
    
    def _add_console_handler(self):
        """Add console handler with human-readable formatting"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self._get_log_level(self.log_level))
        
        # Use simple format for console
        console_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        console_formatter = logging.Formatter(console_format)
        console_handler.setFormatter(console_formatter)
        
        self.logger.addHandler(console_handler)
    
    def _add_file_handler(self):
        """Add rotating file handler with JSON formatting"""
        # Create log directory if it doesn't exist
        log_dir_path = Path(self.log_dir)
        log_dir_path.mkdir(parents=True, exist_ok=True)
        
        # Create log file path
        log_file_path = log_dir_path / self.log_file
        
        # Create rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            filename=str(log_file_path),
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(self._get_log_level(self.log_level))
        
        # Use JSON formatter for file logs
        if self.enable_json:
            json_format = '%(timestamp)s %(level)s %(name)s %(message)s'
            json_formatter = CustomJsonFormatter(json_format)
            file_handler.setFormatter(json_formatter)
        else:
            # Use standard format if JSON is disabled
            file_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            file_formatter = logging.Formatter(file_format)
            file_handler.setFormatter(file_formatter)
        
        self.logger.addHandler(file_handler)
    
    def get_logger(self) -> logging.Logger:
        """
        Get the configured logger instance
        
        Returns:
            Configured logger
        """
        return self.logger
    
    def debug(self, message: str, metadata: Optional[Dict[str, Any]] = None, **kwargs):
        """Log debug message with optional metadata"""
        self._log_with_metadata(logging.DEBUG, message, metadata or {})
    
    def info(self, message: str, metadata: Optional[Dict[str, Any]] = None, **kwargs):
        """Log info message with optional metadata"""
        self._log_with_metadata(logging.INFO, message, metadata or {})
    
    def warning(self, message: str, metadata: Optional[Dict[str, Any]] = None, **kwargs):
        """Log warning message with optional metadata"""
        self._log_with_metadata(logging.WARNING, message, metadata or {})
    
    def error(self, message: str, metadata: Optional[Dict[str, Any]] = None, **kwargs):
        """Log error message with optional metadata"""
        self._log_with_metadata(logging.ERROR, message, metadata or {})
    
    def critical(self, message: str, metadata: Optional[Dict[str, Any]] = None, **kwargs):
        """Log critical message with optional metadata"""
        self._log_with_metadata(logging.CRITICAL, message, metadata or {})
    
    def _log_with_metadata(self, level: int, message: str, metadata: Dict[str, Any]):
        """
        Log message with metadata
        
        Args:
            level: Logging level
            message: Log message
            metadata: Additional metadata to include
        """
        # Make a copy to avoid modifying the original
        metadata = metadata.copy()
        
        # Extract special fields
        task_id = metadata.pop('task_id', None)
        dag_id = metadata.pop('dag_id', None)
        run_id = metadata.pop('run_id', None)
        
        # Create extra dict for LogRecord
        extra = {}
        if task_id:
            extra['task_id'] = task_id
        if dag_id:
            extra['dag_id'] = dag_id
        if run_id:
            extra['run_id'] = run_id
        if metadata:
            extra['metadata'] = metadata
        
        # Log with extra fields
        self.logger.log(level, message, extra=extra)


def get_logger(
    name: str,
    log_dir: Optional[str] = None,
    log_level: Optional[str] = None,
    **kwargs
) -> 'PipelineLogger':
    """
    Factory function to get a configured logger
    
    Args:
        name: Logger name (typically __name__)
        log_dir: Directory for log files
        log_level: Logging level
        **kwargs: Additional arguments for PipelineLogger
    
    Returns:
        PipelineLogger instance with convenience methods
    
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Pipeline started", metadata={"task_id": "bronze_ingestion", "rows": 1000})
    """
    pipeline_logger = PipelineLogger(
        name=name,
        log_dir=log_dir,
        log_level=log_level,
        **kwargs
    )
    return pipeline_logger


def setup_airflow_logging(
    dag_id: str,
    task_id: str,
    run_id: str,
    log_dir: Optional[str] = None
) -> logging.Logger:
    """
    Setup logging for Airflow tasks with DAG context
    
    Args:
        dag_id: Airflow DAG ID
        task_id: Airflow task ID
        run_id: Airflow run ID
        log_dir: Directory for log files
    
    Returns:
        Configured logger with Airflow context
    
    Example:
        >>> logger = setup_airflow_logging(
        ...     dag_id="healthcare_etl_pipeline",
        ...     task_id="bronze_ingest_patients",
        ...     run_id="scheduled__2025-01-15T02:00:00+00:00"
        ... )
    """
    logger_name = f"{dag_id}.{task_id}"
    logger = get_logger(logger_name, log_dir=log_dir)
    
    # Add context to all log records from this logger
    old_factory = logging.getLogRecordFactory()
    
    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.dag_id = dag_id
        record.task_id = task_id
        record.run_id = run_id
        return record
    
    logging.setLogRecordFactory(record_factory)
    
    return logger


def cleanup_old_logs(log_dir: Optional[str] = None, retention_days: int = DEFAULT_RETENTION_DAYS):
    """
    Clean up log files older than retention period
    
    Args:
        log_dir: Directory containing log files
        retention_days: Number of days to retain logs
    """
    log_dir = log_dir or os.getenv('LOG_DIR', DEFAULT_LOG_DIR)
    log_dir_path = Path(log_dir)
    
    if not log_dir_path.exists():
        return
    
    # Get current time
    now = datetime.now()
    
    # Find and delete old log files
    deleted_count = 0
    for log_file in log_dir_path.glob('*.log*'):
        # Get file modification time
        file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
        
        # Calculate age in days
        age_days = (now - file_mtime).days
        
        # Delete if older than retention period
        if age_days > retention_days:
            try:
                log_file.unlink()
                deleted_count += 1
            except Exception as e:
                print(f"Failed to delete old log file {log_file}: {e}", file=sys.stderr)
    
    if deleted_count > 0:
        print(f"Cleaned up {deleted_count} old log files from {log_dir}")


if __name__ == '__main__':
    """
    Test the logging module
    """
    # Create test logger
    logger = get_logger(__name__, log_level='DEBUG')
    
    # Test different log levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    # Test with metadata
    logger.info(
        "Processing data",
        extra={
            'task_id': 'test_task',
            'dag_id': 'test_dag',
            'metadata': {
                'rows_processed': 1000,
                'execution_time': 12.5,
                'status': 'success'
            }
        }
    )
    
    print("\nLog file created at: logs/pipeline.log")
    print("Check the file for JSON formatted logs")
