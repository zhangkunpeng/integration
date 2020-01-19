import multiprocessing
import os
import psutil
import re
import signal
import time
import json

from integration.build import shell
from integration.common import context, log
from integration.common.exception import *

SUCCESS = 0
FAIL = 1
SKIP = 2

ABSOLUTE_MAX_WORKERS = 4


class BaseBuild(object):
    DISTRO = "base"
    ROOTDIR = None
    WORKDIR = None
    LOCAL_REPO_DIR = None

    def __new__(cls, *args, **kwargs):
        from integration.build.centos import CentosBuild
        for c in BaseBuild.__subclasses__():
            if c.DISTRO == os.environ.get('DISTRO', 'base'):
                return object.__new__(c)
        return object.__new__(cls)

    def __init__(self, pkg, rootdir=None, source=None, index=None, **kwargs):
        self.pkg = pkg
        self.__class__.ROOTDIR = rootdir
        self.source = source
        self.pkgdir = os.path.join(source, pkg)
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


class BuildChain(object):

    def __init__(self, source, rootdir, max_workers=1, pkglist_filename=None, pkglist=None, output=None, **kwargs):
        self.max_workers = min(max_workers, ABSOLUTE_MAX_WORKERS)
        self.source = source
        self.rootdir = rootdir
        self.output = output
        self.pkglist_filename = pkglist_filename
        self.package_list = pkglist or []
        self.packages = context.Context()
        self.procdata = []
        self.builds = {}
        log.info(json.dumps(self.__dict__, indent=4))

    def fetch_source(self):
        if re.match(r'(?:http|ftp)s?://', self.source, re.I):
            dirname = os.path.basename(self.source)
            shell.git_checkout(self.source, dist_dir=os.path.join(self.rootdir, dirname))
            self.source = os.path.join(self.rootdir, dirname)
        if not os.path.isdir(self.source):
            raise DirNotExistException(self.source)

    def fetch_package_list(self):
        if self.pkglist_filename:
            filepath = os.path.join(self.source, self.pkglist_filename)
            if not os.path.isfile(filepath):
                raise FileNotExistException(filepath)
            with open(filepath, 'r') as f:
                plist = [n.strip() for n in f.readlines() if n.strip() not in self.package_list]
                self.package_list.extend(plist)
        if not self.package_list:
            log.warn('No Packages To Be Built')

    def signal_handler(self):
        def build_handler(signum, frame):
            for wd in self.procdata:
                p = wd['proc']
                p.terminate()
            pid = os.getpid()
            proc = psutil.Process(pid)
            proc.terminate()
            proc.wait()
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except OSError as e:
                log.warn(e)

        signal.signal(signal.SIGTERM, build_handler)
        signal.signal(signal.SIGINT, build_handler)
        signal.signal(signal.SIGHUP, build_handler)
        signal.signal(signal.SIGABRT, build_handler)

    def build_packages(self, to_build_list):
        from integration.build.centos import CentosBuild
        self.signal_handler()
        for pkg in to_build_list:
            index = self.get_free_process_index()
            while index is None:
                self.monitor_procdata()
                time.sleep(0.1)
                index = self.get_free_process_index()
            log.info("------ Start build %s in process %d ------", pkg, index)
            if pkg not in self.builds:
                self.builds[pkg] = BaseBuild(pkg, source=os.path.join(self.source, pkg), index=index, rootdir=self.rootdir)
            p = multiprocessing.Process(target=BaseBuild.do_build, args=(self.builds[pkg],))
            self.procdata.append({'proc': p, 'build': self.builds[pkg]})
            p.start()
        while len(self.procdata) > 0:
            self.monitor_procdata()
            time.sleep(0.1)

    def build_iteration(self):
        num_of_tries = 0
        to_build_list = self.package_list
        while to_build_list:
            num_of_tries = num_of_tries + 1
            log.info("===== iteration %d start =====", num_of_tries)
            self.build_packages(to_build_list)
            old_build_list = to_build_list[:]
            to_build_list = [pkg for pkg in self.builds.keys() if not self.builds[pkg].success]
            if len(old_build_list) == len(to_build_list):
                if self.max_workers <= 1:
                    break
                else:
                    log.info("Try again with only one process")
                    self.max_workers = 1
        self.result()

    def monitor_procdata(self):
        for pd in self.procdata:
            p = pd['proc']
            result = p.exitcode
            if result is None:
                continue
            p.join()
            build = pd['build']
            if result == SUCCESS:
                log.info("%s] Success Build", build.pkg.rjust(20))
                build.success = True
                build.update_repo(max_workers=self.max_workers)
            elif result == FAIL:
                log.warn("%s] Error Build. Try to build again if other packages will succeed.", build.pkg.rjust(17))
            elif result == SKIP:
                log.info("%s] Skipping already built pkg", build.pkg.rjust(20))
                build.success = True
            else:
                log.error("%s] Unknown exist code %d", build.pkg.rjust(20), result)
                del self.builds[build.pkg]
            self.procdata.remove(pd)

    def get_free_process_index(self):
        busy_index = [b['build'].index for b in self.procdata]
        for i in range(self.max_workers):
            if i not in busy_index:
                return i

    def result(self):
        failed = [b.pkg for b in self.builds.values() if not b.success]
        success = [b.pkg for b in self.builds.values() if b.success]
        if failed:
            log.warn('''
*** Build Failed ***
following pkgs are successfully built:
%s

following pkgs could not be successfully built:
%s
*** Build Failed ***
            ''', '\n'.join(success), '\n'.join(failed))
        else:
            log.info('''
*** Build Successfully ***
following pkgs are successfully built:
%s
*** Build Successfully ***
            ''', '\n'.join(success))
