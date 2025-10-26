"""
Alerting Module

This module provides email notification functionality for the healthcare ETL pipeline.
It implements alert severity levels, templates for different error types, and
configurable alert recipients.
"""

import os
import smtplib
import json
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Any
from pathlib import Path

# Import centralized logger
from logger import get_logger

# Configure logging
logger = get_logger(__name__)


# Alert severity levels
class AlertSeverity:
    """Alert severity levels"""
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


# Alert types
class AlertType:
    """Alert types for different error scenarios"""
    PIPELINE_FAILURE = "PIPELINE_FAILURE"
    DATA_QUALITY_FAILURE = "DATA_QUALITY_FAILURE"
    DATABASE_CONNECTION_ERROR = "DATABASE_CONNECTION_ERROR"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    TRANSFORMATION_ERROR = "TRANSFORMATION_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    PERFORMANCE_DEGRADATION = "PERFORMANCE_DEGRADATION"


class AlertManager:
    """
    Manages alerts and notifications for the ETL pipeline
    """
    
    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        from_email: Optional[str] = None,
        alert_recipients: Optional[List[str]] = None,
        enable_email: bool = True,
        alert_log_dir: Optional[str] = None
    ):
        """
        Initialize the alert manager
        
        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            smtp_user: SMTP username
            smtp_password: SMTP password
            from_email: Sender email address
            alert_recipients: List of recipient email addresses
            enable_email: Enable email notifications
            alert_log_dir: Directory to store alert logs
        """
        self.smtp_host = smtp_host or os.getenv('SMTP_HOST', 'localhost')
        self.smtp_port = smtp_port or int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = smtp_user or os.getenv('SMTP_USER', '')
        self.smtp_password = smtp_password or os.getenv('SMTP_PASSWORD', '')
        self.from_email = from_email or os.getenv('ALERT_FROM_EMAIL', 'etl-alerts@hospital.com')
        
        # Parse recipients from environment variable (comma-separated)
        default_recipients = os.getenv('ALERT_RECIPIENTS', 'data-team@hospital.com')
        self.alert_recipients = alert_recipients or [r.strip() for r in default_recipients.split(',')]
        
        self.enable_email = enable_email and os.getenv('ENABLE_EMAIL_ALERTS', 'true').lower() == 'true'
        self.alert_log_dir = alert_log_dir or os.getenv('ALERT_LOG_DIR', 'logs/alerts')
        
        # Create alert log directory
        Path(self.alert_log_dir).mkdir(parents=True, exist_ok=True)
        
        logger.info(
            "Alert manager initialized",
            metadata={
                'smtp_host': self.smtp_host,
                'smtp_port': self.smtp_port,
                'from_email': self.from_email,
                'recipients': self.alert_recipients,
                'email_enabled': self.enable_email
            }
        )
    
    def send_alert(
        self,
        alert_type: str,
        severity: str,
        subject: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
        recipients: Optional[List[str]] = None
    ) -> bool:
        """
        Send an alert notification
        
        Args:
            alert_type: Type of alert (from AlertType)
            severity: Alert severity (from AlertSeverity)
            subject: Email subject line
            message: Alert message body
            metadata: Additional metadata to include
            recipients: Optional list of recipients (overrides default)
        
        Returns:
            True if alert was sent successfully, False otherwise
        """
        from datetime import timezone
        
        alert_data = {
            'alert_type': alert_type,
            'severity': severity,
            'subject': subject,
            'message': message,
            'metadata': metadata or {},
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'recipients': recipients or self.alert_recipients
        }
        
        # Log alert
        self._log_alert(alert_data)
        
        # Send email if enabled
        if self.enable_email:
            try:
                return self._send_email_alert(alert_data)
            except Exception as e:
                logger.error(
                    f"Failed to send email alert: {str(e)}",
                    metadata={'alert_type': alert_type, 'error': str(e)}
                )
                return False
        else:
            logger.info(
                "Email alerts disabled, alert logged only",
                metadata={'alert_type': alert_type, 'severity': severity}
            )
            return True
    
    def _log_alert(self, alert_data: Dict[str, Any]):
        """
        Log alert to file
        
        Args:
            alert_data: Alert data dictionary
        """
        try:
            # Create alert filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            alert_file = Path(self.alert_log_dir) / f"alert_{timestamp}.json"
            
            # Write alert to file
            with open(alert_file, 'w') as f:
                json.dump(alert_data, f, indent=2)
            
            logger.info(
                f"Alert logged to {alert_file}",
                metadata={'alert_file': str(alert_file), 'alert_type': alert_data['alert_type']}
            )
        
        except Exception as e:
            logger.error(
                f"Failed to log alert to file: {str(e)}",
                metadata={'error': str(e)}
            )
    
    def _send_email_alert(self, alert_data: Dict[str, Any]) -> bool:
        """
        Send email alert via SMTP
        
        Args:
            alert_data: Alert data dictionary
        
        Returns:
            True if email was sent successfully, False otherwise
        """
        try:
            # Create email message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[{alert_data['severity']}] {alert_data['subject']}"
            msg['From'] = self.from_email
            msg['To'] = ', '.join(alert_data['recipients'])
            
            # Create email body
            text_body = self._create_text_email_body(alert_data)
            html_body = self._create_html_email_body(alert_data)
            
            # Attach both plain text and HTML versions
            msg.attach(MIMEText(text_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                # Use TLS if credentials are provided
                if self.smtp_user and self.smtp_password:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                
                server.send_message(msg)
            
            logger.info(
                f"Email alert sent successfully",
                metadata={
                    'alert_type': alert_data['alert_type'],
                    'severity': alert_data['severity'],
                    'recipients': alert_data['recipients']
                }
            )
            return True
        
        except smtplib.SMTPException as e:
            logger.error(
                f"SMTP error sending email alert: {str(e)}",
                metadata={'error': str(e), 'smtp_host': self.smtp_host}
            )
            return False
        
        except Exception as e:
            logger.error(
                f"Unexpected error sending email alert: {str(e)}",
                metadata={'error': str(e)}
            )
            return False
    
    def _create_text_email_body(self, alert_data: Dict[str, Any]) -> str:
        """
        Create plain text email body
        
        Args:
            alert_data: Alert data dictionary
        
        Returns:
            Plain text email body
        """
        body = f"""
Healthcare ETL Pipeline Alert

Alert Type: {alert_data['alert_type']}
Severity: {alert_data['severity']}
Timestamp: {alert_data['timestamp']}

Message:
{alert_data['message']}

"""
        
        # Add metadata if present
        if alert_data.get('metadata'):
            body += "\nAdditional Details:\n"
            for key, value in alert_data['metadata'].items():
                body += f"  {key}: {value}\n"
        
        body += "\n---\nThis is an automated alert from the Healthcare ETL Pipeline.\n"
        
        return body
    
    def _create_html_email_body(self, alert_data: Dict[str, Any]) -> str:
        """
        Create HTML email body
        
        Args:
            alert_data: Alert data dictionary
        
        Returns:
            HTML email body
        """
        # Determine color based on severity
        severity_colors = {
            AlertSeverity.CRITICAL: '#dc3545',
            AlertSeverity.WARNING: '#ffc107',
            AlertSeverity.INFO: '#17a2b8'
        }
        color = severity_colors.get(alert_data['severity'], '#6c757d')
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: {color}; color: white; padding: 15px; border-radius: 5px 5px 0 0; }}
        .content {{ background-color: #f8f9fa; padding: 20px; border: 1px solid #dee2e6; border-top: none; }}
        .metadata {{ background-color: white; padding: 15px; margin-top: 15px; border-radius: 5px; }}
        .metadata-item {{ margin: 5px 0; }}
        .footer {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #dee2e6; font-size: 12px; color: #6c757d; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>Healthcare ETL Pipeline Alert</h2>
        </div>
        <div class="content">
            <p><strong>Alert Type:</strong> {alert_data['alert_type']}</p>
            <p><strong>Severity:</strong> <span style="color: {color}; font-weight: bold;">{alert_data['severity']}</span></p>
            <p><strong>Timestamp:</strong> {alert_data['timestamp']}</p>
            
            <h3>Message:</h3>
            <p>{alert_data['message']}</p>
"""
        
        # Add metadata if present
        if alert_data.get('metadata'):
            html += """
            <div class="metadata">
                <h4>Additional Details:</h4>
"""
            for key, value in alert_data['metadata'].items():
                html += f'                <div class="metadata-item"><strong>{key}:</strong> {value}</div>\n'
            
            html += """
            </div>
"""
        
        html += """
        </div>
        <div class="footer">
            <p>This is an automated alert from the Healthcare ETL Pipeline.</p>
        </div>
    </div>
</body>
</html>
"""
        
        return html
    
    def send_pipeline_failure_alert(
        self,
        pipeline_name: str,
        task_name: str,
        error_message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send alert for pipeline failure
        
        Args:
            pipeline_name: Name of the pipeline
            task_name: Name of the failed task
            error_message: Error message
            metadata: Additional metadata
        
        Returns:
            True if alert was sent successfully
        """
        subject = f"Pipeline Failure: {pipeline_name} - {task_name}"
        message = f"""
The ETL pipeline has failed.

Pipeline: {pipeline_name}
Task: {task_name}
Error: {error_message}

Please investigate and resolve the issue.
"""
        
        return self.send_alert(
            alert_type=AlertType.PIPELINE_FAILURE,
            severity=AlertSeverity.CRITICAL,
            subject=subject,
            message=message,
            metadata=metadata
        )
    
    def send_data_quality_alert(
        self,
        layer: str,
        validation_name: str,
        failure_details: Dict[str, Any]
    ) -> bool:
        """
        Send alert for data quality failure
        
        Args:
            layer: Data layer (Bronze, Silver, Gold)
            validation_name: Name of the validation
            failure_details: Details of the failure
        
        Returns:
            True if alert was sent successfully
        """
        subject = f"Data Quality Failure: {layer} Layer - {validation_name}"
        message = f"""
Data quality validation has failed in the {layer} layer.

Validation: {validation_name}
Success Rate: {failure_details.get('success_rate', 'N/A')}%
Failed Validations: {failure_details.get('failed_count', 'N/A')}

Please review the data quality report for details.
"""
        
        return self.send_alert(
            alert_type=AlertType.DATA_QUALITY_FAILURE,
            severity=AlertSeverity.CRITICAL,
            subject=subject,
            message=message,
            metadata=failure_details
        )
    
    def send_database_connection_alert(
        self,
        database: str,
        error_message: str,
        retry_count: int
    ) -> bool:
        """
        Send alert for database connection error
        
        Args:
            database: Database name
            error_message: Error message
            retry_count: Number of retry attempts
        
        Returns:
            True if alert was sent successfully
        """
        subject = f"Database Connection Error: {database}"
        message = f"""
Failed to connect to the database after {retry_count} attempts.

Database: {database}
Error: {error_message}

Please check database availability and connection parameters.
"""
        
        return self.send_alert(
            alert_type=AlertType.DATABASE_CONNECTION_ERROR,
            severity=AlertSeverity.CRITICAL,
            subject=subject,
            message=message,
            metadata={'database': database, 'retry_count': retry_count}
        )
    
    def send_performance_alert(
        self,
        task_name: str,
        execution_time: float,
        threshold: float
    ) -> bool:
        """
        Send alert for performance degradation
        
        Args:
            task_name: Name of the task
            execution_time: Actual execution time in seconds
            threshold: Expected threshold in seconds
        
        Returns:
            True if alert was sent successfully
        """
        subject = f"Performance Degradation: {task_name}"
        message = f"""
Task execution time exceeded the expected threshold.

Task: {task_name}
Execution Time: {execution_time:.2f} seconds
Threshold: {threshold:.2f} seconds
Difference: {execution_time - threshold:.2f} seconds ({((execution_time / threshold - 1) * 100):.1f}% slower)

Please investigate potential performance issues.
"""
        
        return self.send_alert(
            alert_type=AlertType.PERFORMANCE_DEGRADATION,
            severity=AlertSeverity.WARNING,
            subject=subject,
            message=message,
            metadata={
                'task_name': task_name,
                'execution_time': execution_time,
                'threshold': threshold
            }
        )


# Global alert manager instance
_alert_manager = None


def get_alert_manager(**kwargs) -> AlertManager:
    """
    Get or create the global alert manager instance
    
    Args:
        **kwargs: Arguments to pass to AlertManager constructor
    
    Returns:
        AlertManager instance
    """
    global _alert_manager
    
    if _alert_manager is None:
        _alert_manager = AlertManager(**kwargs)
    
    return _alert_manager


if __name__ == '__main__':
    """
    Test the alerting module
    """
    # Create alert manager
    alert_manager = AlertManager(enable_email=False)  # Disable email for testing
    
    # Test different alert types
    print("Testing alert system...\n")
    
    # Test pipeline failure alert
    alert_manager.send_pipeline_failure_alert(
        pipeline_name="healthcare_etl_pipeline",
        task_name="bronze_ingest_patients",
        error_message="File not found: patients.csv",
        metadata={'source_dir': '/data/source', 'expected_files': 9}
    )
    print("✓ Pipeline failure alert sent\n")
    
    # Test data quality alert
    alert_manager.send_data_quality_alert(
        layer="Silver",
        validation_name="silver_validation_checkpoint",
        failure_details={
            'success_rate': 85.5,
            'failed_count': 3,
            'total_validations': 20
        }
    )
    print("✓ Data quality alert sent\n")
    
    # Test database connection alert
    alert_manager.send_database_connection_alert(
        database="healthcare_warehouse",
        error_message="Connection timeout",
        retry_count=3
    )
    print("✓ Database connection alert sent\n")
    
    # Test performance alert
    alert_manager.send_performance_alert(
        task_name="silver_transform_encounters",
        execution_time=125.5,
        threshold=60.0
    )
    print("✓ Performance alert sent\n")
    
    print(f"All alerts logged to: {alert_manager.alert_log_dir}")
