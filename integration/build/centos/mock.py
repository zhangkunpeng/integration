import os
import json
import shutil
import subprocess
from integration.build import shell
from integration.build.api import env
from integration.common import log

# mock_cfg = '/etc/mock/starlingx.cfg'

# all of the variables below are substituted by the build system
__VERSION__ = "1.4.21"
PYTHONDIR = "/usr/lib/python3.6/site-packages"
PKGPYTHONDIR = "/usr/lib/python3.6/site-packages/mockbuild"
MOCKCONFDIR = '/etc/mock'

MAX_MEM_PER_WORKER = 11
MIN_MEM_PER_WORKER = 3

# end build system subs
config_opts = None


def init_config_opts():
    global config_opts
    if not config_opts:
        import mockbuild.util
        root_cfg = os.path.join(MOCKCONFDIR, '%s.cfg' % os.environ.get('SYSTEM'))
        config_opts = mockbuild.util.load_config(MOCKCONFDIR, root_cfg, None, __VERSION__, PKGPYTHONDIR)


class Mock(object):

    def __init__(self, index, workdir=None, local_repo=None, **kwargs):
        init_config_opts()
        self.config_opts = config_opts
        self.index = index
        self.workdir = workdir
        if local_repo:
            self.add_local_repo(local_repo)
        if self.workdir:
            self.set_mock_env(self.workdir)
        self.config_dir = os.path.join(self.workdir, 'configs')
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir, mode=0o755)
        self.config_file = os.path.join(self.config_dir, '%s.b%d.cfg' % (os.environ.get('SYSTEM'), self.index))
        self.create_mock_conf_file()
        log.info(json.dumps(self.__dict__, indent=4))

    def add_local_repo(self, local_repo_dir):
        localyumrepo = """
[%s]
name=%s
baseurl=%s
enabled=1
skip_if_unavailable=1
metadata_expire=0
cost=1
best=1
""" % ('local_build_repo', 'local_build_repo', "file://%s" % local_repo_dir)
        self.config_opts['yum.conf'] += localyumrepo

    def set_mock_env(self, basedir):
        self.config_opts['basedir'] = basedir
        self.config_opts['resultdir'] = '{0}/result'.format(basedir)
        self.config_opts['backup_base_dir'] = '{0}/backup'.format(basedir)
        self.config_opts['root'] = 'mock/b{0}'.format(self.index)
        self.config_opts['cache_topdir'] = '{0}/cache/b{1}'.format(basedir, self.index)
        self.config_opts['macros']['%_tis_dist'] = '.%s' % env.postfix
        self.config_opts['macros']['%_tis_build_type'] = env.type
        if self.index > 0:
            self.config_opts['plugin_conf']['tmpfs_enable'] = True
            self.config_opts['plugin_conf']['tmpfs_opts'] = {}
            self.config_opts['plugin_conf']['tmpfs_opts']['required_ram_mb'] = 1024
            self.config_opts['plugin_conf']['tmpfs_opts']['max_fs_size'] = "%dg" % MAX_MEM_PER_WORKER
            self.config_opts['plugin_conf']['tmpfs_opts']['mode'] = '0755'
            self.config_opts['plugin_conf']['tmpfs_opts']['keep_mounted'] = True
        if not os.path.isdir(self.config_opts['cache_topdir']):
            os.makedirs(self.config_opts['cache_topdir'], exist_ok=True)
        cache_dir = "%s/%s/mock" % (self.config_opts['basedir'], self.config_opts['root'])
        if not os.path.isdir(cache_dir):
            os.makedirs(cache_dir)

    def create_mock_conf_file(self):
        with open(self.config_file, 'w') as br_dest:
            for k, v in list(self.config_opts.items()):
                br_dest.write("config_opts[%r] = %r\n" % (k, v))
        with open(self.config_file) as f:
            code = compile(f.read(), self.config_file, 'exec')
        # pylint: disable=exec-used
        exec(code)

        # these files needed from the mock.config dir to make mock run
        for fn in ['site-defaults.cfg', 'logging.ini']:
            pth = os.path.join(self.config_dir, fn)
            src = os.path.join(MOCKCONFDIR, fn)
            if os.path.exists(src) and not os.path.exists(pth):
                shutil.copyfile(src, pth)

    def execute(self, srpm_file, result_dir=None, defines=None):
        cmd = ['/usr/bin/mock',
               '--configdir', self.config_dir,
               '-r', self.config_file,
               '--no-clean',
               '--no-cleanup-after',
               '--rebuild']
        if result_dir:
            cmd.extend(['--resultdir', result_dir])
        if defines:
            for k, v in defines.items():
                cmd.extend(['--define', "'%s %s'" % (k, v)])
        cmd.append(srpm_file)
        return shell.popen_communicate(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)





