import logging
from pathlib import Path

def setup_logger(name="mail_pii", log_file=None):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    if log_file:
        file_handler = logging.FileHandler(Path(log_file))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger