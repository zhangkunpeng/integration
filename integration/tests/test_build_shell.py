import os
import tempfile
import unittest
from unittest.mock import patch
from integration.build import shell
from integration.tests import test_common


class ShellCase(unittest.TestCase):

    workdir = None
    @classmethod
    def setUpClass(cls):
        test_common.LogCase.setUpClass()
        cls.workdir = tempfile.TemporaryDirectory()
        cls.envfile = os.path.join(cls.workdir.name, 'envfile')
        with open(cls.envfile, 'w') as f:
            f.write("PARAM1=$PARAM/1\nPARAM2=\"$PARAM/2 \\\n $PARAM1\"")
            f.flush()
        cls.env = {'PARAM': "test"}

    @classmethod
    def tearDownClass(cls):
        test_common.LogCase.tearDownClass()
        cls.workdir.cleanup()

    @patch('integration.build.shell.check_call')
    def test_git_checkout(self, mock_check_call):
        dist_dir = os.path.join(self.workdir.name, 'abc')
        mock_check_call.side_effect = lambda cmd, **kwargs: os.makedirs(cmd[-1])
        shell.git_checkout("http://abc", dist_dir=dist_dir)

        self.assertEqual(True, os.path.exists(dist_dir), "git checkout failed")

    @patch('integration.build.shell.check_output')
    def test_git_commit_count(self, mock_check_output):
        mock_check_output.return_value = "10"
        ret = shell.git_commit_count(self.workdir.name, None)
        self.assertEqual(10, ret, "fetch git commit count failed")

    @patch('integration.build.shell.check_output')
    def test_git_commit_count_with_None(self, mock_check_output):
        mock_check_output.return_value = None
        ret = shell.git_commit_count(self.workdir.name, None)
        self.assertEqual(0, ret, "fetch git commit count failed")

    @patch('integration.build.shell.check_output')
    def test_git_plus_by_status_modified(self, mock_check_output):
        mock_check_output.return_value = "11"
        ret = shell.git_plus_by_status(self.workdir.name)
        self.assertEqual(1, ret)

    @patch('integration.build.shell.check_output')
    def test_git_plus_by_status_unmodified(self, mock_check_output):
        mock_check_output.return_value = None
        ret = shell.git_plus_by_status(self.workdir.name)
        self.assertEqual(0, ret)

    def test_1_echo_env(self):
        param1 = shell.echo_env(self.envfile, self.env, "PARAM1")
        self.assertEqual("test/1", param1)
        param2 = shell.echo_env(self.envfile, self.env, "PARAM2")
        self.assertEqual("test/2 test/1", param2)

    def test_fetch_all_params(self):
        ret = shell.fetch_all_params(self.envfile, self.env)
        self.assertEqual({'PARAM1': "test/1", 'PARAM2': "test/2 test/1"}, ret)

    @patch('integration.build.shell.check_call')
    def test_patch_apply(self, mock_check_call):
        mock_check_call.return_value = 0
        ret = shell.patch_apply(self.envfile, self.workdir.name)
        self.assertEqual(0, ret)


if __name__ == '__main__':
    unittest.main()
