import os
import time
import logging




def init(logfile):
    os.makedirs(os.path.dirname(logfile), exist_ok=True)
    logging.basicConfig(filename=logfile,
                        format='%(asctime)s %(levelname)s %(process)s %(name)s %(funcName)s %(lineno)d %(message)s',
                        level=logging.DEBUG)
    _logger = logging.getLogger('init')
    _logger.debug("logger init")
    latest_log_file = os.path.join(os.path.dirname(logfile), 'latest.log')
    if os.path.exists(latest_log_file):
        os.unlink(latest_log_file)
    os.symlink(logfile, latest_log_file)


def getLogger(name, file=None, std=True):
    formatter = logging.Formatter("%(asctime)s %(levelname)8s %(name)s %(funcName)s %(message)s")
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    if file:
        file_handler = logging.FileHandler(filename=file)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        file_handler.set_name(name)
        logger.addHandler(file_handler)
    if std:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.set_name('console')
        console_handler.setLevel(logging.INFO)
        logger.addHandler(console_handler)
    return logger

