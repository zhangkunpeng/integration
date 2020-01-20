import os
from integration.common import log
SUCCESS = 0
FAIL = 1
SKIP = 2


class BaseBuild(object):
    DISTRO = "base"
    ROOTDIR = None
    WORKDIR = None
    LOCAL_REPO_DIR = None

    # def __new__(cls, *args, **kwargs):
    #     from integration.build.centos import CentosBuild
    #     for c in BaseBuild.__subclasses__():
    #         print(c, c.DISTRO, os.environ.get('DISTRO', 'base'))
    #         if c.DISTRO == os.environ.get('DISTRO', 'base'):
    #             return c.__new__(*args, **kwargs)
    #     return object.__new__(cls)

    def __init__(self, pkg, rootdir=None, source=None, index=None, **kwargs):
        self.pkg = pkg
        self.__class__.ROOTDIR = rootdir
        self.pkgdir = source
        self.name = os.path.basename(self.pkg)
        self.__class__.WORKDIR = os.path.join(self.ROOTDIR, self.__class__.__name__)
        self.build_dir = os.path.join(self.WORKDIR, self.name)
        self.index = index
        self.success = False
        self.success_flag_file = os.path.join(self.build_dir, 'success')
        self.fail_flag_file = os.path.join(self.build_dir, 'fail')
        self.version = None
        self.release = None

    def mark_success(self):
        with open(self.success_flag_file, 'w') as f:
            f.write('DONE')
            f.flush()

    def mark_fail(self):
        with open(self.fail_flag_file, 'w') as f:
            f.write('DONE')
            f.flush()

    def do_build(self):
        if self.is_already_success():
            exit(SKIP)
        try:
            self.prepare_source()
            self.compile()
            exit(SUCCESS)
        except Exception as e:
            log.error(e)
            exit(FAIL)

    def is_already_success(self):
        return os.path.exists(self.success_flag_file)

    def prepare_source(self):
        log.info('%s prepare_source', self.DISTRO)

    def compile(self):
        log.info('%s compile', self.DISTRO)

    def update_repo(self, max_workers=None):
        pass

    def mkdirs(self, *dirs):
        for d in dirs:
            if not os.path.isdir(d):
                os.makedirs(d)

    def fullname(self):
        return '%s-%s-%s' % (self.name, self.version, self.release)



