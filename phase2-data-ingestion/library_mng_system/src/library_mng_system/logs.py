import logging

logger = logging.getLogger("data_validation")
logger.setLevel(logging.INFO)

# handle console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

formatter = logging.Formatter("%(levelname)s: %(message)s")
console_handler.setFormatter(formatter)

if not logger.hasHandlers():
    logger.addHandler(console_handler)

# export logger
__all__ = ["logger"]