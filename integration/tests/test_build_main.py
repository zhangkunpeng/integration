import unittest
from integration.build import main
from integration.common.context import Context


class MainCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    def setUp(self):
        self.ctxt = Context()

    def test_inspect_arguments(self):
        try:
            main.inspect_arguments(self.ctxt)
            assert False
        except Exception:
            assert True

        for k, h in main.fields:
            self.ctxt[k] = h

        try:
            main.inspect_arguments(self.ctxt)
            assert True
        except Exception:
            assert False


if __name__ == '__main__':
    unittest.main()
