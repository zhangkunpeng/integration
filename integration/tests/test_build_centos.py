import unittest
import tempfile
import os
from unittest.mock import patch
from integration.build.centos import mock as m
from integration.build.build import BaseBuild
from integration.build.api import env
from integration.tests.test_common import BaseCase


class MockCase(BaseCase):

    def setUp(self):
        self.workdir = tempfile.TemporaryDirectory()
        env.SYSTEM = 'starlingx'

    def tearDown(self):
        self.workdir.cleanup()

    @patch('integration.build.centos.mock.init_config_opts')
    def test_mock(self, mock_init_config_opts):
        mock_init_config_opts.side_effect = m.config_opts = {'yum.conf': "", 'macros': {}}
        mock = m.Mock(0, workdir=self.workdir.name, local_repo=self.workdir.name)
        self.assertEqual(0, mock.index)
        self.assertIn('yum.conf', m.config_opts)
        self.assertEqual(True, os.path.exists(mock.config_dir))
        self.assertEqual(True, os.path.exists(mock.config_file))

    @patch('integration.build.centos.mock.init_config_opts')
    @patch('integration.build.shell.popen_communicate', return_value=0)
    def test_execute(self, mock_popen_communicate, mock_init_config_opts):
        mock_popen_communicate.return_value = 0
        mock_init_config_opts.side_effect = m.config_opts = {'yum.conf': ""}
        mock = m.Mock(0, workdir=self.workdir.name, local_repo=self.workdir.name)
        ret = mock.execute('srpm_file', result_dir='result-dir', defines={'release': '2020'})
        self.assertEqual(0, ret)
        self.assertIn('srpm_file', mock_popen_communicate.call_args[0][0])
        self.assertIn('result-dir', mock_popen_communicate.call_args[0][0])
        self.assertIn('\'release 2020\'', mock_popen_communicate.call_args[0][0])


class CentosBuildCase(BaseCase):

    def setUp(self):
        self.source = tempfile.TemporaryDirectory()
        self.rootdir = tempfile.TemporaryDirectory()
        env.mirror = self.rootdir.name

    def tearDown(self):
        self.rootdir.cleanup()
        self.source.cleanup()

    @patch('integration.build.centos.mock.init_config_opts')
    def test_create_centosbuild(self, mock_init_config_opts):
        mock_init_config_opts.side_effect = m.config_opts = {'yum.conf': ""}
        os.environ.setdefault('DISTRO', 'centos')
        centos = BaseBuild('testpkg', source=self.source.name, index=0, rootdir=self.rootdir.name)
        self.assertEqual('centos', centos.DISTRO)
        self.assertEqual(0, centos.mock.index)
        self.assertEqual(True, os.path.exists(centos.mock.config_dir))
        self.assertEqual(True, os.path.exists(centos.mock.config_file))

    @patch('integration.build.centos.mock.init_config_opts')
    def test_create_centosbuild_do_build(self, mock_init_config_opts):
        mock_init_config_opts.side_effect = m.config_opts = {'yum.conf': ""}
        os.environ.setdefault('DISTRO', 'centos')
        centos = BaseBuild('testpkg', source=self.source.name, index=0, rootdir=self.rootdir.name)
        self.assertEqual('centos', centos.DISTRO)
        self.assertEqual(0, centos.mock.index)
        self.assertEqual(True, os.path.exists(centos.mock.config_dir))
        self.assertEqual(True, os.path.exists(centos.mock.config_file))


if __name__ == '__main__':
    unittest.main()
