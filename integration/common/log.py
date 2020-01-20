import logging
import logging.handlers
import os
import multiprocessing
import psutil
from integration.common.exception import CriticalException

logger = None


def CONF(name, logdir=os.getcwd(), console=True):
    logfile = os.path.join(logdir, '%s.log' % name)
    if not os.path.exists(os.path.dirname(logfile)):
        os.makedirs(os.path.dirname(logfile))
    formatter = logging.Formatter("%(asctime)s %(levelname)8s %(process)s %(message)s")
    global logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.set_name('console')
        console_handler.setLevel(logging.INFO)
        logger.addHandler(console_handler)
    file_handler = logging.FileHandler(filename=logfile)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    file_handler.set_name(name)
    logger.addHandler(file_handler)
    return logger


def info(msg, *args, **kwargs):
    pid = os.getpid()
    p = psutil.Process(pid)
    p.name()
    logger.info('%s %s' % (p.name(),msg), *args, **kwargs)


def debug(msg, *args, **kwargs):
    logger.debug(msg, *args, **kwargs)


def warn(msg, *args, **kwargs):
    logger.warning(msg, *args, **kwargs)


def error(msg, *args, **kwargs):
    logger.error(msg, *args, **kwargs)


def critical(msg, *args, **kwargs):
    if logger:
        logger.critical(msg, *args, **kwargs)
    raise CriticalException(msg, *args, **kwargs)
