"""
Logging Utilities
Centralized logging functionality for the Clockify application
"""

import logging
import os
import sys
from datetime import datetime
from typing import Optional, Union
from enum import Enum


class LogLevel(Enum):
    """Log level enumeration"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Logger:
    """Centralized logger for the application"""
    
    def __init__(self, name: str = "clockify_app", log_file: Optional[str] = None, 
                 console_output: bool = True, log_level: Union[str, LogLevel] = LogLevel.INFO):
        """
        Initialize logger
        
        Args:
            name: Logger name
            log_file: Optional log file path
            console_output: Whether to output to console
            log_level: Logging level
        """
        self.name = name
        self.logger = logging.getLogger(name)
        
        # Set log level
        if isinstance(log_level, LogLevel):
            level = getattr(logging, log_level.value)
        else:
            level = getattr(logging, log_level.upper())
        self.logger.setLevel(level)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # File handler
        if log_file:
            # Create logs directory if it doesn't exist
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def debug(self, message: str, *args, **kwargs):
        """Log debug message"""
        self.logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """Log info message"""
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """Log warning message"""
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """Log error message"""
        self.logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """Log critical message"""
        self.logger.critical(message, *args, **kwargs)
    
    def log_step(self, step_name: str, status: str = "START"):
        """Log step execution"""
        symbol = "🟢" if status == "START" else "✅" if status == "COMPLETE" else "❌"
        self.info(f"{symbol} {step_name} - {status}")
    
    def log_api_request(self, method: str, url: str, status_code: Optional[int] = None):
        """Log API request"""
        if status_code:
            self.debug(f"API {method} {url} - Status: {status_code}")
        else:
            self.debug(f"API {method} {url}")
    
    def log_export(self, filename: str, record_count: Optional[int] = None):
        """Log data export"""
        if record_count is not None:
            self.info(f"📁 Exported {record_count} records to: {filename}")
        else:
            self.info(f"📁 Exported data to: {filename}")
    
    def log_configuration(self, config_name: str, status: str):
        """Log configuration validation"""
        symbol = "✅" if status == "VALID" else "❌" if status == "INVALID" else "⚠️"
        self.info(f"{symbol} Configuration {config_name}: {status}")
    
    def log_access_operation(self, operation: str, target: str, success: bool = True):
        """Log access management operations"""
        symbol = "🔓" if operation.upper() == "GRANT" else "🔒"
        status = "SUCCESS" if success else "FAILED"
        status_symbol = "✅" if success else "❌"
        self.info(f"{symbol} {operation.upper()} access for {target} - {status_symbol} {status}")
    
    def set_level(self, level: Union[str, LogLevel]):
        """Change logging level"""
        if isinstance(level, LogLevel):
            log_level = getattr(logging, level.value)
        else:
            log_level = getattr(logging, level.upper())
        self.logger.setLevel(log_level)
    
    def create_log_file_for_session(self, base_name: str = "clockify_session") -> str:
        """Create a timestamped log file for current session"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"logs/{base_name}_{timestamp}.log"
        
        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)
        
        # Add file handler for this session
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        self.info(f"Session log file created: {log_filename}")
        return log_filename


# Default logger instance
default_logger = Logger()


# Convenience functions for quick logging
def debug(message: str, *args, **kwargs):
    """Quick debug log"""
    default_logger.debug(message, *args, **kwargs)


def info(message: str, *args, **kwargs):
    """Quick info log"""
    default_logger.info(message, *args, **kwargs)


def warning(message: str, *args, **kwargs):
    """Quick warning log"""
    default_logger.warning(message, *args, **kwargs)


def error(message: str, *args, **kwargs):
    """Quick error log"""
    default_logger.error(message, *args, **kwargs)


def critical(message: str, *args, **kwargs):
    """Quick critical log"""
    default_logger.critical(message, *args, **kwargs)


def log_step(step_name: str, status: str = "START"):
    """Quick step log"""
    default_logger.log_step(step_name, status)


def log_export(filename: str, record_count: Optional[int] = None):
    """Quick export log"""
    default_logger.log_export(filename, record_count) 