import logging
import time

from colorlog import ColoredFormatter

# Logger setup
t = time.localtime()
fmt_time = time.strftime("%Y-%m-%d %H:%M:%S", t) # format time


def get_logger(
        *, 
        name: str="default_logger", 
        logfile: str=f"logs/default_logger_{fmt_time}.log",
        level: logging._Level=logging.DEBUG
    ):

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    file_handler = logging.FileHandler(logfile)
    file_handler.setLevel(level)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(
        ColoredFormatter(
            "%(log_color)s%(levelname)s%(reset)s %(message)s",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            }
        )
    )

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False
    return logger

logger = get_logger()