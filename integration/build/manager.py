
import multiprocessing
import importlib
from integration.build import Builder
import os
from integration.common.log import getLogger
from integration.common.context import Context
import re
from integration.build import shell
from integration.common import log

_log = None

_ctxt = Context()


def init(context):
    _ctxt.update(context)
    global _log
    _log = getLogger('manager')

    _ctxt.builder = fetch_builder_class(_ctxt.os)
    _ctxt.source = fetch_source(_ctxt.source, _ctxt.rootdir)


def fetch_builder_class(module=None):
    package = 'integration.build'
    if module:
        package = '%s.%s' % (package, module)
    try:
        mod = importlib.import_module(package)
        for name in dir(mod):
            c = getattr(mod, name)
            if type(c) == type:
                for base in c.__bases__:
                    if base == Builder:
                        return c
    except ModuleNotFoundError:
        return Builder


def fetch_source(source, rootdir):
    if re.match(r'(?:http|ftp)s?://', source, re.I):
        dirname = os.path.basename(source)
        shell.git_checkout(source, dist_dir=os.path.join(rootdir, dirname))
        source = os.path.join(rootdir, dirname)
    if not os.path.isdir(source):
        raise Exception('Source %s does not exist' % source)
    return source




class BuildManager(object):

    def __init__(self, module=None, processes=None):
        self.module = 'integration.build'
        if module:
            self.module = '%s.%s' % (self.module, module)
        self.processes = processes
        self.failed_list = []

    def new_builder(self, *args, **kwargs):
        try:
            module = importlib.import_module(self.module)
            for name in dir(module):
                c = getattr(module, name)
                if type(c) == type:
                    for base in c.__bases__:
                        if base == Builder:
                            return c(*args, **kwargs)
        except ModuleNotFoundError:
            return Builder(*args, **kwargs)

    def on_build_process_finished(self, builder):
        if builder.success:
            log.info("BUILD SUCCESS : %s", builder.pkg)
        else:
            self.failed_list.append(builder.pkg)
            log.error("BUILD FAILED : %s", builder.pkg)

    def do_build(self, builder):
        return builder

    def start_build(self, build_list, processes):
        pool = multiprocessing.Pool(processes=processes)
        for pkg in build_list:
            builder = self.new_builder(pkg)
            pool.apply_async(func=self.do_build, args=(builder,), callback=self.on_build_process_finished)
        pool.close()
        pool.join()

    def build_iteration(self, build_list):
        try_times = 0
        to_build_list = build_list
        while to_build_list:
            try_times += 1
            log.info("===== iteration %d start =====", try_times)
            self.start_build(to_build_list, self.processes)
            old_build_list = to_build_list[:]
            to_build_list = self.failed_list
            if len(old_build_list) == len(to_build_list):
                if self.processes <= 1:
                    break
                self.processes = 1
                log.info("Try again with only one process")
        self.output()
    
    def output(self):
        log.info('OUTPUT')
