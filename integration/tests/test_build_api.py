import unittest, tempfile
from integration.tests.test_common import BaseCase
from integration.build import env
from integration.build import api


class APICase(BaseCase):

    def setUp(self):
        self.source = tempfile.TemporaryDirectory()
        self.rootdir = tempfile.TemporaryDirectory()
        env.rootdir = self.rootdir.name

    def tearDown(self):
        self.source.cleanup()
        self.rootdir.cleanup()

    def test_exec(self):
        api.exec(source=self.source.name,
                 rootdir=self.rootdir.name,
                 mirror=self.rootdir.name,
                 release='20.01',
                 type='std',
                 output=self.rootdir.name,
                 DISTRO='base',
                 SYSTEM='starlingx',
                 pkglist=['test1', 'test2'])
        assert True


if __name__ == '__main__':
    unittest.main()
