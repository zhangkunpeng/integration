import unittest


class ManagerCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    def test_new_builder(self):
        self.assertEqual(True, False)


if __name__ == '__main__':
    unittest.main()
