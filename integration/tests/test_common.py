import os
import unittest

from integration.common import exception, log


class BaseCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        log.CONF('test', logdir=os.getcwd(), console=False)

    @classmethod
    def tearDownClass(cls):
        for handler in log.logger.handlers:
            handler.close()


class LogCase(BaseCase):

    def test_log_info(self):
        try:
            log.info("%s %d", "test for info", 1)
            assert True
        except Exception as e:
            assert False

    def test_log_debug(self):
        try:
            log.debug("%s %d", "test for debug", 1)
            assert True
        except Exception as e:
            assert False

    def test_log_warn(self):
        try:
            log.warn("%s %d", "test for debug", 1)
            assert True
        except Exception as e:
            assert False

    def test_log_error(self):
        try:
            log.error("%s %d", "test for debug", 1)
            assert True
        except Exception as e:
            assert False

    def test_log_critical(self):
        try:
            log.critical("%s %d", "test for debug", 1)
            assert True
        except exception.CriticalException:
            assert True
        except Exception:
            assert False


if __name__ == '__main__':
    unittest.main()
