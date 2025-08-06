"""
import logging

logger = logging.getLogger("data_validation")
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

formatter = logging.Formatter("%(levelname)s: %(message)s")
console_handler.setFormatter(formatter)

if not logger.handlers:
    logger.addHandler(console_handler)

__all__ = ["logger"]
"""

import logging

logger = logging.getLogger("data_validation")
logger.setLevel(logging.INFO)

# Formatter for all handlers
formatter = logging.Formatter("%(levelname)s: %(message)s")

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# Add handlers only once
if not logger.handlers:
    logger.addHandler(console_handler)

def set_log_level(level_name: str):
    """
    Dynamically sets log level based on CLI argument (e.g., INFO, DEBUG, WARNING).
    """
    level = getattr(logging, level_name.upper(), logging.INFO)
    logger.setLevel(level)
    console_handler.setLevel(level)

    # Optional: Add file logging (commented out by default)
    # file_handler = logging.FileHandler("invalid_data.log")
    # file_handler.setFormatter(formatter)
    # file_handler.setLevel(level)
    # logger.addHandler(file_handler)

__all__ = ["logger", "set_log_level"]
