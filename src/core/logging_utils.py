"""Comprehensive logging and error handling utilities for Catalyst.

This module provides:
- Global logging configuration
- Universal error decorator for exception tracking
- Contextual error reporting utilities
- Model selection error helpers
"""

import logging
import functools
import traceback
import inspect
import sys
from pathlib import Path
from typing import Any, Callable, Optional, Dict, List
from datetime import datetime


def setup_logging(level: int = logging.INFO, log_file: Optional[str] = None) -> None:
    """
    Configure global logging with comprehensive format and optional file output.
    
    Args:
        level: Logging level (logging.DEBUG, logging.INFO, etc.)
        log_file: Optional file path for log output
    """
    # Create formatter with comprehensive context
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d (%(funcName)s) - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    root_logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        try:
            # Ensure log directory exists
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            file_handler.setLevel(level)
            root_logger.addHandler(file_handler)
            
            logging.info("Logging configured with file output: %s", log_file)
        except Exception as e:
            logging.warning("Failed to setup file logging to %s: %s", log_file, str(e))
    
    logging.info("Catalyst logging system initialized at level: %s", logging.getLevelName(level))


def log_exceptions(func: Callable) -> Callable:
    """
    Universal decorator that catches exceptions and logs full traceback with context.
    
    Usage:
        @log_exceptions
        def my_function(arg1, arg2):
            # Function implementation
            pass
    
    Args:
        func: Function to wrap with exception logging
        
    Returns:
        Wrapped function with exception logging
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Get caller context
            caller_frame = inspect.currentframe().f_back
            caller_info = ""
            if caller_frame:
                caller_info = f" (called from {caller_frame.f_code.co_filename}:{caller_frame.f_lineno} in {caller_frame.f_code.co_name})"
            
            # Format arguments for logging (safely)
            args_repr = _safe_repr_args(args, kwargs)
            
            # Log comprehensive error information
            logger.error(
                "Exception in %s%s:\n"
                "Arguments: %s\n"
                "Exception: %s: %s\n"
                "Traceback:\n%s",
                func.__name__,
                caller_info,
                args_repr,
                type(e).__name__,
                str(e),
                traceback.format_exc()
            )
            
            # Re-raise the exception
            raise
    
    return wrapper


def _safe_repr_args(args: tuple, kwargs: dict, max_length: int = 200) -> str:
    """
    Safely create string representation of function arguments.
    
    Args:
        args: Positional arguments
        kwargs: Keyword arguments
        max_length: Maximum length of representation
        
    Returns:
        Safe string representation of arguments
    """
    try:
        args_str = []
        
        # Handle positional args
        for i, arg in enumerate(args):
            try:
                arg_repr = repr(arg)
                if len(arg_repr) > 100:
                    arg_repr = f"{type(arg).__name__}(...)"
                args_str.append(f"arg{i}={arg_repr}")
            except Exception:
                args_str.append(f"arg{i}=<repr_failed>")
        
        # Handle keyword args
        for key, value in kwargs.items():
            try:
                value_repr = repr(value)
                if len(value_repr) > 100:
                    value_repr = f"{type(value).__name__}(...)"
                args_str.append(f"{key}={value_repr}")
            except Exception:
                args_str.append(f"{key}=<repr_failed>")
        
        result = ", ".join(args_str)
        
        # Truncate if too long
        if len(result) > max_length:
            result = result[:max_length-3] + "..."
            
        return result
        
    except Exception:
        return "<args_repr_failed>"


def log_model_selection_error(
    provider: str,
    requested_model: str,
    available_models: Dict[str, str],
    caller_context: Optional[str] = None
) -> None:
    """
    Log detailed model selection errors with context.
    
    Args:
        provider: Provider name (openai, gemini, etc.)
        requested_model: Model key that was requested
        available_models: Dictionary of available models
        caller_context: Optional additional context about the caller
    """
    logger = logging.getLogger(__name__)
    
    # Get caller information automatically
    caller = inspect.stack()[1]
    caller_info = f"{caller.filename}:{caller.lineno} in {caller.function}"
    
    if caller_context:
        caller_info += f" ({caller_context})"
    
    # Format available models for display
    available_list = list(available_models.keys()) if available_models else ["None"]
    
    logger.error(
        "Model selection failed for provider '%s':\n"
        "  Requested: %s\n"
        "  Available: %s\n"
        "  Called from: %s\n"
        "  Available models: %s",
        provider,
        requested_model,
        available_list,
        caller_info,
        available_models
    )


def log_api_error(
    provider: str,
    operation: str,
    error: Exception,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log API errors with provider and operation context.
    
    Args:
        provider: API provider name
        operation: Operation that failed
        error: Exception that occurred
        context: Optional additional context
    """
    logger = logging.getLogger(__name__)
    
    context_str = ""
    if context:
        try:
            context_items = [f"{k}={v}" for k, v in context.items()]
            context_str = f"\n  Context: {', '.join(context_items)}"
        except Exception:
            context_str = "\n  Context: <context_repr_failed>"
    
    logger.error(
        "API Error in %s provider during %s:\n"
        "  Error: %s: %s%s\n"
        "  Traceback:\n%s",
        provider,
        operation,
        type(error).__name__,
        str(error),
        context_str,
        traceback.format_exc()
    )


def log_config_error(
    config_type: str,
    config_path: str,
    error: Exception,
    suggestion: Optional[str] = None
) -> None:
    """
    Log configuration loading errors with helpful suggestions.
    
    Args:
        config_type: Type of configuration (e.g., "model config", "pipeline config")
        config_path: Path to the configuration file
        error: Exception that occurred
        suggestion: Optional suggestion for fixing the issue
    """
    logger = logging.getLogger(__name__)
    
    suggestion_str = ""
    if suggestion:
        suggestion_str = f"\n  Suggestion: {suggestion}"
    
    logger.error(
        "Configuration Error loading %s from %s:\n"
        "  Error: %s: %s%s\n"
        "  Traceback:\n%s",
        config_type,
        config_path,
        type(error).__name__,
        str(error),
        suggestion_str,
        traceback.format_exc()
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def log_pipeline_step(
    step_name: str,
    status: str,
    duration: Optional[float] = None,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log pipeline step execution with status and timing.
    
    Args:
        step_name: Name of the pipeline step
        status: Status (started, completed, failed, etc.)
        duration: Optional execution duration in seconds
        details: Optional additional details
    """
    logger = logging.getLogger(__name__)
    
    timing_str = ""
    if duration is not None:
        timing_str = f" (took {duration:.2f}s)"
    
    details_str = ""
    if details:
        try:
            details_items = [f"{k}={v}" for k, v in details.items()]
            details_str = f" - {', '.join(details_items)}"
        except Exception:
            details_str = " - <details_repr_failed>"
    
    log_level = logging.INFO
    if status.lower() in ['failed', 'error']:
        log_level = logging.ERROR
    elif status.lower() in ['warning', 'warn']:
        log_level = logging.WARNING
    
    logger.log(
        log_level,
        "Pipeline step '%s' %s%s%s",
        step_name,
        status,
        timing_str,
        details_str
    )


class CatalystLogger:
    """
    Context manager for structured logging in specific operations.
    
    Usage:
        with CatalystLogger("operation_name") as logger:
            logger.info("Starting operation")
            # Do work
            logger.success("Operation completed")
    """
    
    def __init__(self, operation_name: str, logger_name: Optional[str] = None):
        """
        Initialize context logger.
        
        Args:
            operation_name: Name of the operation being logged
            logger_name: Optional specific logger name
        """
        self.operation_name = operation_name
        self.logger = logging.getLogger(logger_name or __name__)
        self.start_time = None
    
    def __enter__(self):
        """Start the logging context."""
        self.start_time = datetime.now()
        self.logger.info("Starting operation: %s", self.operation_name)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End the logging context."""
        duration = (datetime.now() - self.start_time).total_seconds()
        
        if exc_type is None:
            self.logger.info(
                "Completed operation: %s (took %.2fs)", 
                self.operation_name, 
                duration
            )
        else:
            self.logger.error(
                "Failed operation: %s (took %.2fs) - %s: %s", 
                self.operation_name, 
                duration,
                exc_type.__name__,
                str(exc_val)
            )
    
    def info(self, message: str, *args, **kwargs):
        """Log info message with operation context."""
        self.logger.info(f"[{self.operation_name}] {message}", *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """Log warning message with operation context."""
        self.logger.warning(f"[{self.operation_name}] {message}", *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """Log error message with operation context."""
        self.logger.error(f"[{self.operation_name}] {message}", *args, **kwargs)
    
    def success(self, message: str, *args, **kwargs):
        """Log success message with operation context."""
        self.logger.info(f"[{self.operation_name}] ✅ {message}", *args, **kwargs)