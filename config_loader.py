"""
Configuration Loader Module

This module provides functionality to load and validate pipeline configuration
from YAML files with environment variable substitution.
"""

import os
import re
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, Union
from datetime import datetime

# Import centralized logger
from logger import get_logger

# Configure logging
logger = get_logger(__name__)


class ConfigurationError(Exception):
    """Custom exception for configuration errors"""
    pass


class ConfigLoader:
    """
    Configuration loader with environment variable substitution and validation.
    
    This class loads YAML configuration files and performs:
    - Environment variable substitution (${VAR_NAME})
    - Configuration validation
    - Default value provision
    - Environment-specific overrides
    """
    
    # Pattern for environment variable substitution
    ENV_VAR_PATTERN = re.compile(r'\$\{([^}]+)\}')
    
    def __init__(self, config_file: str = 'config/pipeline_config.yaml'):
        """
        Initialize configuration loader.
        
        Args:
            config_file: Path to the main configuration YAML file
        
        Raises:
            ConfigurationError: If config file cannot be loaded
        """
        self.config_file = config_file
        self.config = None
        self.environment = os.getenv('ENVIRONMENT', 'development')
        
        logger.info(
            f"Initializing configuration loader",
            metadata={'config_file': config_file, 'environment': self.environment}
        )
        
        # Load configuration
        self._load_config()
        
        # Apply environment-specific overrides
        self._apply_environment_overrides()
        
        # Substitute environment variables in the entire config
        self.config = self._substitute_env_vars(self.config)
        
        # Validate configuration
        self._validate_config()
    
    def _load_config(self) -> None:
        """
        Load YAML configuration file.
        
        Raises:
            ConfigurationError: If file cannot be loaded or parsed
        """
        try:
            config_path = Path(self.config_file)
            
            if not config_path.exists():
                raise ConfigurationError(f"Configuration file not found: {self.config_file}")
            
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            
            if self.config is None:
                raise ConfigurationError(f"Configuration file is empty: {self.config_file}")
            
            logger.info(f"Loaded configuration from {self.config_file}")
            
        except yaml.YAMLError as e:
            error_msg = f"Failed to parse YAML configuration: {str(e)}"
            logger.error(error_msg, metadata={'config_file': self.config_file, 'error': str(e)})
            raise ConfigurationError(error_msg) from e
        
        except Exception as e:
            error_msg = f"Failed to load configuration: {str(e)}"
            logger.error(error_msg, metadata={'config_file': self.config_file, 'error': str(e)})
            raise ConfigurationError(error_msg) from e
    
    def _substitute_env_vars(self, value: Any) -> Any:
        """
        Recursively substitute environment variables in configuration values.
        
        Supports ${VAR_NAME} syntax with optional default values: ${VAR_NAME:default}
        
        Args:
            value: Configuration value (can be string, dict, list, or other)
        
        Returns:
            Value with environment variables substituted
        """
        if isinstance(value, str):
            # Find all environment variable references
            matches = self.ENV_VAR_PATTERN.findall(value)
            
            for match in matches:
                # Check if default value is specified (VAR_NAME:default)
                if ':' in match:
                    var_name, default_value = match.split(':', 1)
                    env_value = os.getenv(var_name.strip(), default_value.strip())
                else:
                    var_name = match
                    env_value = os.getenv(var_name.strip())
                
                # If environment variable is not set and no default, keep original
                if env_value is None:
                    logger.warning(
                        f"Environment variable not set: {var_name}",
                        metadata={'variable': var_name, 'config_value': value}
                    )
                    continue
                
                # Replace the placeholder with the environment value
                placeholder = '${' + match + '}'
                value = value.replace(placeholder, env_value)
            
            # Convert boolean strings
            if value.lower() in ('true', 'yes', 'on', '1'):
                return True
            elif value.lower() in ('false', 'no', 'off', '0'):
                return False
            
            # Convert numeric strings
            try:
                if '.' in value:
                    return float(value)
                else:
                    return int(value)
            except (ValueError, AttributeError):
                pass
            
            return value
        
        elif isinstance(value, dict):
            return {k: self._substitute_env_vars(v) for k, v in value.items()}
        
        elif isinstance(value, list):
            return [self._substitute_env_vars(item) for item in value]
        
        else:
            return value
    
    def _apply_environment_overrides(self) -> None:
        """
        Apply environment-specific configuration overrides.
        
        Looks for 'environments' section in config and applies overrides
        based on the current environment (development, staging, production).
        """
        if 'environments' not in self.config:
            logger.debug("No environment-specific overrides found")
            return
        
        env_overrides = self.config['environments'].get(self.environment)
        
        if not env_overrides:
            logger.debug(f"No overrides for environment: {self.environment}")
            return
        
        logger.info(f"Applying environment overrides for: {self.environment}")
        
        # Deep merge environment overrides into main config
        self._deep_merge(self.config, env_overrides)
    
    def _deep_merge(self, base: Dict, override: Dict) -> None:
        """
        Deep merge override dictionary into base dictionary.
        
        Args:
            base: Base dictionary to merge into (modified in place)
            override: Override dictionary with values to merge
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def _validate_config(self) -> None:
        """
        Validate required configuration parameters.
        
        Raises:
            ConfigurationError: If required parameters are missing or invalid
        """
        logger.info("Validating configuration")
        
        # Required top-level sections
        required_sections = ['pipeline', 'bronze', 'silver', 'gold', 'data_quality']
        
        for section in required_sections:
            if section not in self.config:
                raise ConfigurationError(f"Missing required configuration section: {section}")
        
        # Validate pipeline section
        pipeline_config = self.config['pipeline']
        if 'name' not in pipeline_config or not pipeline_config['name']:
            raise ConfigurationError("Pipeline name is required")
        
        # Validate Bronze configuration
        bronze_config = self.config['bronze']
        if 'tables' not in bronze_config or not bronze_config['tables']:
            raise ConfigurationError("Bronze tables list is required")
        
        # Validate Gold database configuration
        gold_config = self.config['gold']
        if 'database' not in gold_config:
            raise ConfigurationError("Gold database configuration is required")
        
        db_config = gold_config['database']
        required_db_params = ['host', 'port', 'database', 'user']
        for param in required_db_params:
            if param not in db_config or not db_config[param]:
                raise ConfigurationError(f"Database parameter '{param}' is required")
        
        # Validate data quality thresholds
        dq_config = self.config['data_quality']
        if 'failure_handling' in dq_config:
            threshold = dq_config['failure_handling'].get('warning_threshold')
            if threshold is not None:
                try:
                    threshold_float = float(threshold)
                    if not 0 <= threshold_float <= 1:
                        raise ConfigurationError(
                            f"warning_threshold must be between 0 and 1, got: {threshold}"
                        )
                except (ValueError, TypeError):
                    raise ConfigurationError(
                        f"warning_threshold must be a number, got: {threshold}"
                    )
        
        logger.info("Configuration validation passed")
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-separated key path.
        
        Supports nested keys like 'bronze.source_path' or 'data_quality.failure_handling.fail_on_error'
        Environment variables are already substituted during initialization.
        
        Args:
            key_path: Dot-separated path to configuration key
            default: Default value if key not found
        
        Returns:
            Configuration value
        
        Example:
            >>> config = ConfigLoader()
            >>> source_path = config.get('bronze.source_path')
            >>> fail_on_error = config.get('data_quality.failure_handling.fail_on_error', True)
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                logger.debug(
                    f"Configuration key not found: {key_path}, using default: {default}",
                    metadata={'key_path': key_path, 'default': default}
                )
                return default
        
        return value
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get entire configuration section.
        
        Environment variables are already substituted during initialization.
        
        Args:
            section: Top-level section name (e.g., 'bronze', 'silver', 'gold')
        
        Returns:
            Dictionary containing the section configuration
        
        Raises:
            ConfigurationError: If section does not exist
        """
        if section not in self.config:
            raise ConfigurationError(f"Configuration section not found: {section}")
        
        return self.config[section]
    
    def get_bronze_config(self) -> Dict[str, Any]:
        """Get Bronze layer configuration."""
        return self.get_section('bronze')
    
    def get_silver_config(self) -> Dict[str, Any]:
        """Get Silver layer configuration."""
        return self.get_section('silver')
    
    def get_gold_config(self) -> Dict[str, Any]:
        """Get Gold layer configuration."""
        return self.get_section('gold')
    
    def get_data_quality_config(self) -> Dict[str, Any]:
        """Get data quality configuration."""
        return self.get_section('data_quality')
    
    def get_airflow_config(self) -> Dict[str, Any]:
        """Get Airflow DAG configuration."""
        return self.get_section('airflow')
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return self.get_section('logging')
    
    def get_alerting_config(self) -> Dict[str, Any]:
        """Get alerting configuration."""
        return self.get_section('alerting')
    
    def get_database_connection_string(self) -> str:
        """
        Get PostgreSQL database connection string.
        
        Returns:
            Connection string in format: postgresql://user:password@host:port/database
        """
        db_config = self.get_section('gold')['database']
        
        host = db_config['host']
        port = db_config['port']
        database = db_config['database']
        user = db_config['user']
        password = db_config.get('password', '')
        
        if password:
            return f"postgresql://{user}:{password}@{host}:{port}/{database}"
        else:
            return f"postgresql://{user}@{host}:{port}/{database}"
    
    def get_run_date(self) -> str:
        """
        Get run date for the pipeline.
        
        Returns current date in YYYY-MM-DD format if not specified in config.
        
        Returns:
            Run date string in YYYY-MM-DD format
        """
        run_date = self.get('defaults.run_date')
        
        if run_date is None or run_date == 'null':
            run_date = datetime.now().strftime('%Y-%m-%d')
            logger.debug(f"Using current date as run_date: {run_date}")
        
        return run_date
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """
        Check if a feature flag is enabled.
        
        Args:
            feature_name: Name of the feature flag
        
        Returns:
            True if feature is enabled, False otherwise
        """
        return self.get(f'features.{feature_name}', False)
    
    def get_table_list(self) -> list:
        """
        Get list of tables to process.
        
        Returns:
            List of table names
        """
        return self.get('bronze.tables', [])
    
    def get_task_timeout(self, task_type: str) -> int:
        """
        Get timeout for a specific task type.
        
        Args:
            task_type: Type of task (e.g., 'bronze_ingestion', 'silver_transformation')
        
        Returns:
            Timeout in seconds
        """
        return self.get(f'airflow.task_timeouts.{task_type}', self.get('defaults.timeout_seconds', 1800))
    
    def get_benchmark(self, benchmark_name: str) -> Optional[float]:
        """
        Get performance benchmark value.
        
        Args:
            benchmark_name: Name of the benchmark
        
        Returns:
            Benchmark value in seconds, or None if not found
        """
        return self.get(f'performance.benchmarks.{benchmark_name}')
    
    def should_fail_on_data_quality_error(self) -> bool:
        """
        Check if pipeline should fail on data quality errors.
        
        Returns:
            True if should fail, False otherwise
        """
        return self.get('data_quality.failure_handling.fail_on_error', True)
    
    def get_data_quality_warning_threshold(self) -> float:
        """
        Get data quality warning threshold.
        
        Returns:
            Warning threshold as a decimal (e.g., 0.05 for 5%)
        """
        return self.get('data_quality.failure_handling.warning_threshold', 0.05)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Get entire configuration as dictionary.
        
        Environment variables are already substituted during initialization.
        
        Returns:
            Complete configuration dictionary
        """
        return self.config
    
    def __repr__(self) -> str:
        """String representation of ConfigLoader."""
        return f"ConfigLoader(config_file='{self.config_file}', environment='{self.environment}')"


# Global configuration instance (lazy loaded)
_config_instance: Optional[ConfigLoader] = None


def get_config(config_file: str = 'config/pipeline_config.yaml', reload: bool = False) -> ConfigLoader:
    """
    Get global configuration instance (singleton pattern).
    
    Args:
        config_file: Path to configuration file
        reload: Force reload of configuration
    
    Returns:
        ConfigLoader instance
    
    Example:
        >>> from config_loader import get_config
        >>> config = get_config()
        >>> bronze_path = config.get('bronze.source_path')
    """
    global _config_instance
    
    if _config_instance is None or reload:
        # Load environment variables if not already loaded
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            logger.warning("python-dotenv not installed, environment variables must be set manually")
        
        _config_instance = ConfigLoader(config_file)
    
    return _config_instance


def load_config_from_file(config_file: str) -> Dict[str, Any]:
    """
    Load configuration from file and return as dictionary.
    
    This is a convenience function for one-time config loading without
    creating a ConfigLoader instance.
    
    Args:
        config_file: Path to YAML configuration file
    
    Returns:
        Configuration dictionary with environment variables substituted
    
    Raises:
        ConfigurationError: If file cannot be loaded
    """
    loader = ConfigLoader(config_file)
    return loader.to_dict()


if __name__ == '__main__':
    """
    Command-line interface for configuration validation and inspection.
    
    Usage:
        python config_loader.py [config_file]
    """
    import sys
    import json
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Get config file from command line or use default
    config_file = 'config/pipeline_config.yaml'
    if len(sys.argv) > 1 and not sys.argv[1].startswith('--'):
        config_file = sys.argv[1]
    
    try:
        print(f"\nLoading configuration from: {config_file}")
        print("="*60)
        
        config = ConfigLoader(config_file)
        
        print(f"\nEnvironment: {config.environment}")
        print(f"Pipeline Name: {config.get('pipeline.name')}")
        print(f"Pipeline Version: {config.get('pipeline.version')}")
        print("\n" + "="*60)
        
        # Display key configuration sections
        print("\nBronze Configuration:")
        print(f"  Source Path: {config.get('bronze.source_path')}")
        print(f"  Target Path: {config.get('bronze.target_path')}")
        print(f"  Tables: {len(config.get_table_list())}")
        
        print("\nSilver Configuration:")
        print(f"  Source Path: {config.get('silver.source_path')}")
        print(f"  Target Path: {config.get('silver.target_path')}")
        print(f"  Compression: {config.get('silver.parquet.compression')}")
        
        print("\nGold Configuration:")
        print(f"  Database: {config.get('gold.database.database')}")
        print(f"  Host: {config.get('gold.database.host')}")
        print(f"  Port: {config.get('gold.database.port')}")
        
        print("\nData Quality Configuration:")
        print(f"  Fail on Error: {config.should_fail_on_data_quality_error()}")
        print(f"  Warning Threshold: {config.get_data_quality_warning_threshold()}")
        
        print("\nFeature Flags:")
        features = config.get_section('features')
        for feature, enabled in features.items():
            status = "✓" if enabled else "✗"
            print(f"  {status} {feature}")
        
        print("\n" + "="*60)
        print("Configuration validation: PASSED")
        print("="*60 + "\n")
        
        # Optionally dump full config as JSON
        if '--dump' in sys.argv:
            print("\nFull Configuration (JSON):")
            print(json.dumps(config.to_dict(), indent=2))
        
        sys.exit(0)
        
    except ConfigurationError as e:
        print(f"\nERROR: {str(e)}\n", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {str(e)}\n", file=sys.stderr)
        sys.exit(1)
