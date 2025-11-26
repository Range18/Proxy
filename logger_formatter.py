import logging
from constants import *


class LoggerFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: RESET,
        logging.INFO: GREEN,
        logging.WARNING: YELLOW,
        logging.ERROR: RED,
        logging.CRITICAL: RED,
    }

    def format(self, record):
        color = self.COLORS.get(record.levelno, RESET)
        message = super().format(record)
        return f"{color}{message}{RESET}"
