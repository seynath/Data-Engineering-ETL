"""
Data Quality Validation Module using Great Expectations

This module provides functions to run Great Expectations checkpoints
for validating Bronze and Silver layer data quality.
"""

import os
import json
import traceback
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

import great_expectations as gx
from great_expectations.core.batch import BatchRequest
from great_expectations.checkpoint import SimpleCheckpoint

# Import centralized logger
from logger import get_logger

# Configure logging
logger = get_logger(__name__)


class DataQualityValidator:
    """
    Data quality validator using Great Expectations framework
    """
    
    def __init__(self, context_root_dir: str = "great_expectations"):
        """
        Initialize the validator with Great Expectations context
        
        Args:
            context_root_dir: Path to Great Expectations project directory
        """
        self.context_root_dir = context_root_dir
        self.context = None
        self._initialize_context()
    
    def _initialize_context(self):
        """Initialize Great Expectations Data Context"""
        try:
            self.context = gx.get_context(context_root_dir=self.context_root_dir)
            logger.info(
                f"Initialized Great Expectations context from {self.context_root_dir}",
                metadata={'context_root_dir': self.context_root_dir}
            )
        except FileNotFoundError as e:
            error_msg = f"Great Expectations directory not found: {self.context_root_dir}"
            logger.error(error_msg, metadata={'context_root_dir': self.context_root_dir, 'error': str(e)})
            raise RuntimeError(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to initialize Great Expectations context: {str(e)}"
            logger.error(
                error_msg,
                metadata={'context_root_dir': self.context_root_dir, 'error': str(e), 'traceback': traceback.format_exc()}
            )
            raise RuntimeError(error_msg) from e
    
    def run_checkpoint(
        self,
        checkpoint_name: str,
        run_name: Optional[str] = None
    ) -> Dict:
        """
        Run a Great Expectations checkpoint
        
        Args:
            checkpoint_name: Name of the checkpoint to run
            run_name: Optional custom run name
            
        Returns:
            Dictionary containing validation results
        
        Raises:
            RuntimeError: If checkpoint execution fails
        """
        if run_name is None:
            run_name = f"{checkpoint_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        start_time = datetime.now()
        
        logger.info(
            f"Running checkpoint: {checkpoint_name}",
            metadata={'checkpoint_name': checkpoint_name, 'run_name': run_name}
        )
        
        try:
            # Get checkpoint
            try:
                checkpoint = self.context.get_checkpoint(checkpoint_name)
            except Exception as e:
                error_msg = f"Checkpoint not found: {checkpoint_name}"
                logger.error(error_msg, metadata={'checkpoint_name': checkpoint_name, 'error': str(e)})
                raise RuntimeError(error_msg) from e
            
            # Run checkpoint
            try:
                results = checkpoint.run(run_name=run_name)
            except Exception as e:
                error_msg = f"Checkpoint execution failed: {checkpoint_name}"
                logger.error(
                    error_msg,
                    metadata={'checkpoint_name': checkpoint_name, 'run_name': run_name, 'error': str(e), 'traceback': traceback.format_exc()}
                )
                raise RuntimeError(error_msg) from e
            
            # Parse results
            try:
                validation_result = self._parse_validation_results(results)
            except Exception as e:
                error_msg = f"Failed to parse validation results: {str(e)}"
                logger.error(error_msg, metadata={'checkpoint_name': checkpoint_name, 'error': str(e)})
                raise RuntimeError(error_msg) from e
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            validation_result['execution_time_seconds'] = execution_time
            
            # Log results
            self._log_validation_results(validation_result)
            
            # Raise alert if validation failed
            if not validation_result['success']:
                self._raise_alert(checkpoint_name, validation_result)
            
            return validation_result
            
        except RuntimeError:
            raise
        except Exception as e:
            error_msg = f"Unexpected error running checkpoint {checkpoint_name}: {str(e)}"
            logger.critical(
                error_msg,
                metadata={'checkpoint_name': checkpoint_name, 'error_type': type(e).__name__, 'error': str(e), 'traceback': traceback.format_exc()}
            )
            raise RuntimeError(error_msg) from e
    
    def validate_bronze_layer(
        self,
        run_date: str,
        run_name: Optional[str] = None
    ) -> Dict:
        """
        Validate Bronze layer data
        
        Args:
            run_date: Date of the data run (YYYY-MM-DD format)
            run_name: Optional custom run name
            
        Returns:
            Dictionary containing validation results
        """
        logger.info(f"Validating Bronze layer for date: {run_date}")
        
        checkpoint_name = "bronze_validation_checkpoint"
        
        if run_name is None:
            run_name = f"bronze_{run_date}"
        
        return self.run_checkpoint(checkpoint_name, run_name)
    
    def validate_silver_layer(
        self,
        run_date: str,
        run_name: Optional[str] = None
    ) -> Dict:
        """
        Validate Silver layer data
        
        Args:
            run_date: Date of the data run (YYYY-MM-DD format)
            run_name: Optional custom run name
            
        Returns:
            Dictionary containing validation results
        """
        logger.info(f"Validating Silver layer for date: {run_date}")
        
        checkpoint_name = "silver_validation_checkpoint"
        
        if run_name is None:
            run_name = f"silver_{run_date}"
        
        return self.run_checkpoint(checkpoint_name, run_name)
    
    def _parse_validation_results(self, results) -> Dict:
        """
        Parse Great Expectations validation results
        
        Args:
            results: Great Expectations checkpoint results
            
        Returns:
            Dictionary with parsed results
        """
        validation_result = {
            'success': results.success,
            'run_id': str(results.run_id),
            'run_time': datetime.now().isoformat(),
            'statistics': {
                'evaluated_validations': 0,
                'successful_validations': 0,
                'unsuccessful_validations': 0,
                'success_percent': 0.0
            },
            'validation_results': []
        }
        
        # Parse individual validation results
        for validation_result_identifier, validation_result_obj in results.run_results.items():
            # Extract the actual validation result from the wrapper
            if isinstance(validation_result_obj, dict) and 'validation_result' in validation_result_obj:
                actual_result = validation_result_obj['validation_result']
            else:
                actual_result = validation_result_obj
            
            # Handle both dict and object access patterns
            if isinstance(actual_result, dict):
                success = actual_result.get('success', False)
                statistics = actual_result.get('statistics', {})
                results_list = actual_result.get('results', [])
            else:
                success = getattr(actual_result, 'success', False)
                statistics = getattr(actual_result, 'statistics', {})
                results_list = getattr(actual_result, 'results', [])
            
            result_dict = {
                'expectation_suite_name': validation_result_identifier.expectation_suite_identifier.expectation_suite_name,
                'success': success,
                'statistics': statistics
            }
            
            # Extract failed expectations
            if not success:
                failed_expectations = []
                for result in results_list:
                    result_success = result.get('success', True) if isinstance(result, dict) else getattr(result, 'success', True)
                    if not result_success:
                        expectation_config = result.get('expectation_config', {}) if isinstance(result, dict) else getattr(result, 'expectation_config', {})
                        result_data = result.get('result', {}) if isinstance(result, dict) else getattr(result, 'result', {})
                        failed_expectations.append({
                            'expectation_type': expectation_config.get('expectation_type', 'unknown'),
                            'kwargs': expectation_config.get('kwargs', {}),
                            'result': {
                                'element_count': result_data.get('element_count'),
                                'unexpected_count': result_data.get('unexpected_count'),
                                'unexpected_percent': result_data.get('unexpected_percent'),
                                'observed_value': result_data.get('observed_value')
                            }
                        })
                result_dict['failed_expectations'] = failed_expectations
            
            validation_result['validation_results'].append(result_dict)
            validation_result['statistics']['evaluated_validations'] += 1
            
            if success:
                validation_result['statistics']['successful_validations'] += 1
            else:
                validation_result['statistics']['unsuccessful_validations'] += 1
        
        # Calculate success percentage
        if validation_result['statistics']['evaluated_validations'] > 0:
            validation_result['statistics']['success_percent'] = (
                validation_result['statistics']['successful_validations'] /
                validation_result['statistics']['evaluated_validations'] * 100
            )
        
        return validation_result
    
    def _log_validation_results(self, validation_result: Dict):
        """
        Log validation results
        
        Args:
            validation_result: Parsed validation results
        """
        stats = validation_result['statistics']
        
        log_message = (
            f"Validation Results - "
            f"Success: {validation_result['success']}, "
            f"Evaluated: {stats['evaluated_validations']}, "
            f"Successful: {stats['successful_validations']}, "
            f"Failed: {stats['unsuccessful_validations']}, "
            f"Success Rate: {stats['success_percent']:.2f}%"
        )
        
        if validation_result['success']:
            logger.info(log_message)
        else:
            logger.error(log_message)
            
            # Log details of failed validations
            for result in validation_result['validation_results']:
                if not result['success']:
                    logger.error(
                        f"Failed validation suite: {result['expectation_suite_name']}"
                    )
                    if 'failed_expectations' in result:
                        for failed_exp in result['failed_expectations']:
                            logger.error(
                                f"  - {failed_exp['expectation_type']}: "
                                f"{failed_exp['kwargs']}"
                            )
    
    def _raise_alert(self, checkpoint_name: str, validation_result: Dict):
        """
        Raise alert for validation failures
        
        Args:
            checkpoint_name: Name of the checkpoint that failed
            validation_result: Parsed validation results
        """
        alert_message = {
            'alert_type': 'DATA_QUALITY_FAILURE',
            'severity': 'CRITICAL',
            'checkpoint': checkpoint_name,
            'timestamp': datetime.now().isoformat(),
            'success_rate': validation_result['statistics']['success_percent'],
            'failed_validations': validation_result['statistics']['unsuccessful_validations'],
            'details': []
        }
        
        # Add details of failed validations
        for result in validation_result['validation_results']:
            if not result['success']:
                alert_message['details'].append({
                    'suite': result['expectation_suite_name'],
                    'failed_expectations': result.get('failed_expectations', [])
                })
        
        # Log alert (in production, this would send to alerting system)
        logger.critical(f"DATA QUALITY ALERT: {json.dumps(alert_message, indent=2)}")
        
        # Write alert to file
        alert_dir = Path("logs/alerts")
        alert_dir.mkdir(parents=True, exist_ok=True)
        
        alert_file = alert_dir / f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(alert_file, 'w') as f:
            json.dump(alert_message, f, indent=2)
        
        logger.info(f"Alert written to {alert_file}")
    
    def generate_data_quality_report(
        self,
        validation_results: List[Dict],
        output_file: str = "logs/data_quality_report.json"
    ):
        """
        Generate a comprehensive data quality report
        
        Args:
            validation_results: List of validation result dictionaries
            output_file: Path to output report file
        """
        report = {
            'report_generated': datetime.now().isoformat(),
            'total_validations': len(validation_results),
            'overall_success': all(r['success'] for r in validation_results),
            'validations': validation_results
        }
        
        # Calculate aggregate statistics
        total_evaluated = sum(r['statistics']['evaluated_validations'] for r in validation_results)
        total_successful = sum(r['statistics']['successful_validations'] for r in validation_results)
        total_failed = sum(r['statistics']['unsuccessful_validations'] for r in validation_results)
        
        report['aggregate_statistics'] = {
            'total_evaluated_validations': total_evaluated,
            'total_successful_validations': total_successful,
            'total_failed_validations': total_failed,
            'overall_success_rate': (total_successful / total_evaluated * 100) if total_evaluated > 0 else 0
        }
        
        # Write report to file
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Data quality report generated: {output_file}")
        logger.info(f"Overall success rate: {report['aggregate_statistics']['overall_success_rate']:.2f}%")
        
        return report


def main():
    """
    Main function for testing data quality validation
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Run data quality validation')
    parser.add_argument(
        '--layer',
        choices=['bronze', 'silver', 'both'],
        default='both',
        help='Which layer to validate'
    )
    parser.add_argument(
        '--date',
        default=datetime.now().strftime('%Y-%m-%d'),
        help='Date of data to validate (YYYY-MM-DD)'
    )
    
    args = parser.parse_args()
    
    # Initialize validator
    validator = DataQualityValidator()
    
    validation_results = []
    
    # Run validations
    if args.layer in ['bronze', 'both']:
        try:
            bronze_result = validator.validate_bronze_layer(args.date)
            validation_results.append(bronze_result)
        except Exception as e:
            logger.error(f"Bronze validation failed: {e}")
    
    if args.layer in ['silver', 'both']:
        try:
            silver_result = validator.validate_silver_layer(args.date)
            validation_results.append(silver_result)
        except Exception as e:
            logger.error(f"Silver validation failed: {e}")
    
    # Generate report
    if validation_results:
        validator.generate_data_quality_report(validation_results)
    
    # Exit with error code if any validation failed
    if not all(r['success'] for r in validation_results):
        exit(1)


if __name__ == "__main__":
    main()
