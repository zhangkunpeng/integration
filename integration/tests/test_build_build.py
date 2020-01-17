import unittest, os
from integration.build.build import BuildChain, BaseBuild
from integration.build import env
from integration.common.exception import *
from integration.tests.test_common import BaseCase
from integration.build import shell
import tempfile
from unittest.mock import patch


class BuildChainCase(BaseCase):

    def setUp(self):
        self.source = tempfile.TemporaryDirectory()
        self.rootdir = tempfile.TemporaryDirectory()
        env.rootdir = self.rootdir.name

    def tearDown(self):
        self.source.cleanup()
        self.rootdir.cleanup()

    def test_fetch_source_local(self):
        try:
            buildchain = BuildChain(os.path.join(self.source.name, "local"), None)
            buildchain.fetch_source()
            assert False
        except DirNotExistException:
            assert True

        try:
            buildchain = BuildChain(self.source.name, None)
            buildchain.fetch_source()
            assert True
        except Exception:
            assert False

    @patch('integration.build.shell.check_call')
    def test_fetch_source_remote(self, mock_check_call):
        mock_check_call.side_effect = lambda cmd, **kwargs: os.makedirs(os.path.join(self.rootdir.name, 'fault.git'))
        buildchain = BuildChain("https://opendev.org/starlingx/fault.git", self.rootdir.name)
        buildchain.fetch_source()
        self.assertEqual(True, os.path.exists(buildchain.source))
        self.assertEqual('fault.git', os.path.basename(buildchain.source))

    def test_fetch_package_list(self):
        # test with pkglist filename
        pkglist_filename = "pkg_dirs"
        with open(os.path.join(self.source.name, pkglist_filename), 'w') as f:
            f.write("bash\ntest/bash\n")
            f.flush()
        try:
            buildchain = BuildChain(self.source.name, self.rootdir.name, pkglist_filename=pkglist_filename)
            buildchain.fetch_source()
            buildchain.fetch_package_list()
            self.assertEqual(['bash', 'test/bash'], buildchain.package_list)
        except Exception:
            assert False
        # test with pkglist
        try:
            buildchain = BuildChain(self.source.name, self.rootdir.name, pkglist=['bash', 'test'])
            buildchain.fetch_source()
            buildchain.fetch_package_list()
            self.assertEqual(['bash', 'test'], buildchain.package_list)
        except Exception:
            assert False
        # test with pkglist and pkglist_filename
        try:
            buildchain = BuildChain(self.source.name, self.rootdir.name, pkglist=['bash', 'test'], pkglist_filename=pkglist_filename)
            buildchain.fetch_source()
            buildchain.fetch_package_list()
            self.assertEqual(['bash', 'test', 'test/bash'], buildchain.package_list)
        except Exception:
            assert False
        # TEST with none
        try:
            buildchain = BuildChain(self.source.name, self.rootdir.name, pkglist=['bash', 'test'], pkglist_filename="test0")
            buildchain.fetch_source()
            buildchain.fetch_package_list()
            assert False
        except FileNotExistException:
            assert True
        except Exception:
            assert False

    @patch('integration.build.build.BaseBuild.do_build')
    def test_build_packages(self, mock_do_build):
        #BaseBuild.do_build = lambda x: exit(0)
        mock_do_build.side_effect = lambda x: exit(0)
        buildchain = BuildChain(self.source.name, self.rootdir.name, pkglist=['test1', 'test2', 'test3'], max_workers=2)
        buildchain.fetch_source()
        buildchain.fetch_package_list()
        self.assertEqual(['test1', 'test2', 'test3'], buildchain.package_list)
        buildchain.build_packages(buildchain.package_list)
        self.assertEqual(3, len(buildchain.builds.keys()))
        self.assertEqual(True, buildchain.builds['test3'].success)
        self.assertEqual(True, buildchain.builds['test2'].success)
        self.assertEqual(True, buildchain.builds['test1'].success)
        self.assertEqual(0, buildchain.builds['test1'].index)
        self.assertEqual(1, buildchain.builds['test2'].index)
        self.assertEqual(0, buildchain.builds['test3'].index)

    @patch('integration.build.build.BaseBuild.do_build')
    def test_build_iteration(self, mock_do_build):
        mock_do_build.side_effect = lambda x: exit(1 if x.pkg == 'test1' else (2 if x.pkg == 'test2' else 0))
        buildchain = BuildChain(self.source.name, self.rootdir.name, pkglist=['test1', 'test2', 'test3'], max_workers=2)
        buildchain.fetch_source()
        buildchain.fetch_package_list()
        self.assertEqual(['test1', 'test2', 'test3'], buildchain.package_list)
        buildchain.build_iteration()
        self.assertEqual(3, len(buildchain.builds.keys()))
        self.assertEqual(True, buildchain.builds['test3'].success)
        self.assertEqual(True, buildchain.builds['test2'].success)
        self.assertEqual(False, buildchain.builds['test1'].success)
        self.assertEqual(0, buildchain.builds['test1'].index)
        self.assertEqual(1, buildchain.builds['test2'].index)
        self.assertEqual(0, buildchain.builds['test3'].index)


if __name__ == '__main__':
    unittest.main()
