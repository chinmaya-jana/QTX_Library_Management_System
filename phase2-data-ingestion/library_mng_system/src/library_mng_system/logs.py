import logging

logger = logging.getLogger("data_validation")
logger.setLevel(logging.INFO)

formatter = logging.Formatter("%(levelname)s: %(message)s")

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

if not logger.handlers:
    logger.addHandler(console_handler)

def set_log_level(level_name: str):
    level = getattr(logging, level_name.upper(), logging.INFO)
    logger.setLevel(level)
    console_handler.setLevel(level)

__all__ = ["logger", "set_log_level"]
