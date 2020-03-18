import os
from integration.common import log
import importlib
SUCCESS = 0
FAIL = 1
SKIP = 2


class BaseBuild(object):
    DISTRO = "base"

    def __init__(self, pkg, source=None, rootdir=None, index=None, type=None, **kwargs):
        self.pkg = pkg
        self.rootdir = rootdir
        self.pkgdir = source
        self.type = type
        self.name = os.path.basename(self.pkg)
        self.workdir = os.path.join(self.rootdir, self.__class__.__name__.lower(), self.type)
        self.index = index
        self.success = False
        self.success_flag_file = os.path.join(self.workdir, 'success')
        self.fail_flag_file = os.path.join(self.workdir, 'fail')
        self.version = None
        self.release = None
        self.mkdirs(self.workdir)

    def mark_success(self):
        with open(self.success_flag_file, 'a') as f:
            f.write('%s\n' % self.pkg)
            f.flush()
        log.info('BUILD SUCCESS')

    def mark_fail(self):
        with open(self.fail_flag_file, 'a') as f:
            f.write('%s\n' % self.pkg)
            f.flush()
        log.info('BUILD FAIL')

    def do_build(self):
        if self.is_already_success():
            exit(SKIP)
        try:
            self.cleanup()
            self.prepare_source()
            self.compile()
            exit(SUCCESS)
        except Exception as e:
            log.error(e)
            exit(FAIL)

    def is_already_success(self):
        with open(self.fail_flag_file, 'r') as f:
            for line in f.readlines():
                if self.pkg == line.strip():
                    return False
        with open(self.success_flag_file, 'r') as f:
            for line in f.readlines():
                if self.pkg == line.strip():
                    return True
        return False

    def prepare_source(self):
        log.info('%s prepare_source', self.DISTRO)

    def compile(self):
        log.info('%s compile', self.DISTRO)

    def cleanup(self):
        pass

    def update_repo(self, max_workers=None):
        pass

    def mkdirs(self, *dirs):
        for d in dirs:
            if not os.path.isdir(d):
                os.makedirs(d)

    def fullname(self):
        return '%s-%s-%s' % (self.name, self.version, self.release)


class Builder(object):

    OS = 'undefined'
    SYSTEM = 'undefined'

    def __init__(self, pkg=None, context=None):
        self.pkg = pkg
        self.context = context
        self.name = os.path.basename(pkg)
        self.version = None
        self.release = None
        self.workdir = os.path.join(context.rootdir, self.__class__.__name__.lower(), context.build_type)
        self.success = False
        self.pkgdir = os.path.join(context.source, pkg)
        self.success_flag_file = os.path.join(self.workdir, 'success')

    def do_build(self, lock, ctxt):
        with lock:
            self.success = self.is_already_success()

    def mark_success(self):
        with open(self.success_flag_file, 'a') as f:
            f.write('%s\n' % self.pkg)
            f.flush()

    def is_already_success(self):
        with open(self.success_flag_file, 'r') as f:
            for line in f.readlines():
                if self.pkg == line.strip():
                    return True
        return False

