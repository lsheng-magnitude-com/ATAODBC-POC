from __future__ import print_function
import logging
import sys
from logging.handlers import RotatingFileHandler


class SingleLevelFilter(logging.Filter):
    """ This class is used for filtering logs based on the level.
    """

    def __init__(self, level, reject=True):
        self.level = level
        self.reject = reject

    def filter(self, record):
        if not self.reject:
            return record.levelno == self.level
        else:
            return record.levelno != self.level


class ExceptionFilter(logging.Filter):
    def __init__(self):
        pass

    def filter(self, record):
        return record.exc_info is None


# Create the filters
reject_critical_filter = SingleLevelFilter(logging.CRITICAL)
exception_filter = ExceptionFilter()

# Create the formatters
file_formatter = logging.Formatter(fmt="%(asctime)s - [%(levelname)s] - [%(name)s] - %(message)s",
                                   datefmt="%Y-%m-%d %H:%M:%S")

# Create and setup the handlers
# File Handler
file_handler = RotatingFileHandler(filename="booster.log", mode="a")
file_handler.setFormatter(file_formatter)
# Standard out handler
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.INFO)
stdout_handler.addFilter(exception_filter)
stdout_handler.addFilter(reject_critical_filter)
# Standard error handler
stderr_handler = logging.StreamHandler(sys.stderr)
stderr_handler.setLevel(logging.CRITICAL)
# Create the root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)


class AtaLog(object):
    """ ATA version log facility
        A wrapper around the python logging
    """

    def __init__(self, name):
        """
        Create a logger with the given name.
        """
        self.logger = logging.getLogger(name)
        # Add handlers to the loggers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(stderr_handler)
        self.logger.addHandler(stdout_handler)

    def __call__(self, msg):
        self.logger.info(msg)

    def info(self, msg):
        self.logger.info(msg)

    def warning(self, msg):
        self.logger.warning(msg)

    def error(self, msg):
        self.logger.error(msg)

    def debug(self, msg):
        self.logger.debug(msg)

    def exception(self, msg):
        self.logger.exception(msg)
        self.logger.error(msg)

    def critical(self, msg):
        self.logger.critical(msg)

    def printHeader(self, headerName):
        """
        Print the header for each tag.
        :return:
        """
        print('=' * 30)
        print('{:^30}'.format('Enter ' + headerName))
        print('=' * 30)
