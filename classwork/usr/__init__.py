from logzero import logger

try:
    from . import classes
except ImportError:
    logger.info("No user defined classes found in `classwork/.usr/classes`")
