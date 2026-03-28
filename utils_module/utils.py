"""
Utility Functions Module

Common utility functions for logging, validation, environment checks,
and other helper operations used across the pipeline.
"""

import logging
import sys
from typing import Optional
from pathlib import Path


def setup_logging(log_level: str = 'INFO') -> None:
    """
    Configure logging for the application.
    
    Sets up console logging with appropriate formatting and level.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    # Ensure log level is valid
    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR']
    if log_level not in valid_levels:
        log_level = 'INFO'
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level))
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


def validate_environment() -> None:
    """
    Validate that all required dependencies are available.
    
    Checks for:
    - Required Python packages (requests, beautifulsoup4, pyyaml)
    - Python version
    
    Raises:
        RuntimeError: If validation fails
    """
    required_packages = {
        'requests': 'requests',
        'bs4': 'beautifulsoup4',
        'yaml': 'pyyaml',
        'PyPDF2': 'PyPDF2'
    }
    
    missing_packages = []
    
    for import_name, package_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        raise RuntimeError(
            f"Missing required packages: {', '.join(missing_packages)}\n"
            f"Install with: pip install {' '.join(missing_packages)}"
        )
    
    # Check Python version
    if sys.version_info < (3, 8):
        raise RuntimeError("Python 3.8+ is required")


def ensure_directory(path: Path) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path
        
    Returns:
        Path object for the directory
        
    Raises:
        OSError: If directory cannot be created
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        return path
    except OSError as e:
        raise OSError(f"Cannot create directory {path}: {e}")


def safe_write_file(filepath: Path, content: str, encoding: str = 'utf-8') -> None:
    """
    Safely write content to a file.
    
    Creates parent directories if necessary and handles errors gracefully.
    
    Args:
        filepath: Path to file
        content: Content to write
        encoding: File encoding (default: utf-8)
        
    Raises:
        IOError: If write fails
    """
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding=encoding) as f:
            f.write(content)
    except IOError as e:
        raise IOError(f"Cannot write to {filepath}: {e}")


def safe_read_file(filepath: Path, encoding: str = 'utf-8') -> str:
    """
    Safely read content from a file.
    
    Args:
        filepath: Path to file
        encoding: File encoding (default: utf-8)
        
    Returns:
        File content as string
        
    Raises:
        IOError: If read fails
    """
    try:
        with open(filepath, 'r', encoding=encoding) as f:
            return f.read()
    except IOError as e:
        raise IOError(f"Cannot read from {filepath}: {e}")


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to remove invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename.strip()


def truncate_text(text: str, max_length: int, ellipsis: str = '...') -> str:
    """
    Truncate text to maximum length with ellipsis.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        ellipsis: Ellipsis string
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(ellipsis)] + ellipsis


def format_size(bytes_size: int) -> str:
    """
    Format byte size to human-readable format.
    
    Args:
        bytes_size: Size in bytes
        
    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.2f} TB"


def count_lines(filepath: Path) -> int:
    """
    Count lines in a file.
    
    Args:
        filepath: Path to file
        
    Returns:
        Number of lines
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return sum(1 for _ in f)
    except Exception as e:
        logging.warning(f"Cannot count lines in {filepath}: {e}")
        return 0
