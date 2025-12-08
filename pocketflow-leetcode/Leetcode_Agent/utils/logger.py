"""
Logging utilities for LeetCode Agent

This module provides logging functionality for the LeetCode agent.
"""

import logging
import os
import sys
from datetime import datetime
from typing import Optional


class LeetCodeLogger:
    """
    Logger class for LeetCode Agent with detailed error reporting.
    """
    
    def __init__(self, name: str = "leetcode_agent", log_level: str = "INFO"):
        """
        Initialize the logger.
        
        Args:
            name: Logger name
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Create logs directory if it doesn't exist
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        # Create file handler with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"leetcode_agent_{timestamp}.log")
        
        # Create file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Create formatter with stack info to show actual caller
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(funcName)s() - %(message)s'
        )
        
        # Add formatter to handlers
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to logger
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
    
    def debug(self, message: str, exc_info: bool = False):
        """Log debug message."""
        self.logger.debug(message, exc_info=exc_info, stacklevel=2)
    
    def info(self, message: str, exc_info: bool = False):
        """Log info message."""
        self.logger.info(message, exc_info=exc_info, stacklevel=2)
    
    def warning(self, message: str, exc_info: bool = False):
        """Log warning message."""
        self.logger.warning(message, exc_info=exc_info, stacklevel=2)
    
    def error(self, message: str, exc_info: bool = True):
        """Log error message with exception info by default."""
        self.logger.error(message, exc_info=exc_info, stacklevel=2)
    
    def critical(self, message: str, exc_info: bool = True):
        """Log critical message with exception info by default."""
        self.logger.critical(message, exc_info=exc_info, stacklevel=2)
    
    def exception(self, message: str):
        """Log exception with traceback."""
        self.logger.exception(message, stacklevel=2)


# Global logger instance
_logger = None


def get_logger(name: Optional[str] = None) -> LeetCodeLogger:
    """
    Get the logger instance.
    
    Args:
        name: Optional logger name
        
    Returns:
        Logger instance
    """
    global _logger
    if _logger is None:
        _logger = LeetCodeLogger(name or "leetcode_agent")
    return _logger


def log_function_call(func):
    """
    Decorator to log function calls.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    def wrapper(*args, **kwargs):
        logger = get_logger()
        logger.debug(f"Calling function {func.__name__} with args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"Function {func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"Function {func.__name__} failed with error: {str(e)}")
            raise
    return wrapper


def log_method_call(cls):
    """
    Class decorator to log all method calls.
    
    Args:
        cls: Class to decorate
        
    Returns:
        Decorated class
    """
    for attr_name in dir(cls):
        attr = getattr(cls, attr_name)
        if callable(attr) and not attr_name.startswith('_'):
            setattr(cls, attr_name, log_function_call(attr))
    return cls