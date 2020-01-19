import unittest, tempfile, os
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

    def test_run(self):
        api.run(source=self.source.name,
                 rootdir=self.rootdir.name,
                 mirror=self.rootdir.name,
                 release='20.01',
                 type='std',
                 output=self.rootdir.name,
                 DISTRO='base',
                 SYSTEM='starlingx',
                 pkglist=['test1', 'test2'])
        assert True

    def test_run_with_pkglist_file(self):
        fd, name = tempfile.mkstemp(dir=self.source.name)
        api.run(source=self.source.name,
                 rootdir=self.rootdir.name,
                 mirror=self.rootdir.name,
                 release='20.01',
                 type='std',
                 output=self.rootdir.name,
                 DISTRO='base',
                 SYSTEM='starlingx',
                 pkg=os.path.basename(name))
        assert True

    def test_run_with_pkglist_dir(self):
        name = tempfile.mkdtemp(dir=self.source.name)
        api.run(source=self.source.name,
                rootdir=self.rootdir.name,
                mirror=self.rootdir.name,
                release='20.01',
                type='std',
                output=self.rootdir.name,
                DISTRO='base',
                SYSTEM='starlingx',
                pkg=os.path.basename(name))
        assert True


if __name__ == '__main__':
    unittest.main()
