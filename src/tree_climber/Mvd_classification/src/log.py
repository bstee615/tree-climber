import logging
import os
from datetime import datetime

def setup_logging(log_file=None, log_level=logging.INFO, console=True):
    """
    Setup logging configuration for the application.

    Args:
        log_file (str): Path to the log file. If None, uses default name with timestamp.
        log_level: Logging level (e.g., logging.DEBUG, logging.INFO)
        console (bool): Whether to also log to console
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file) if log_file else 'logs'
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # If no log_file provided, create one with timestamp
    if log_file is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = os.path.join(log_dir, f'training_{timestamp}.log')

    # Create logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler (optional)
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger

# Convenience function to get logger
def get_logger(name=__name__):
    return logging.getLogger(name)

# Example usage:
# from log import setup_logging
# setup_logging(log_file='my_training.log')
# logger = get_logger()
# logger.info("Training started")
