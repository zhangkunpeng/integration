from .context import Context
from . import logger, manager
from . import shell
import argparse
import os
import re
import time


def prepare_context(context):
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", help="input the project which to build")
    parser.add_argument("--branch", help="the git repo branch")
    parser.add_argument("--type", help="build type", choices=["std", "rt"], default="std")
    parser.add_argument("--rootdir", help="input the root dir")
    parser.add_argument("--os", help="input the operating system")
    parser.add_argument("--mirror", help="input the repo mirror dir")
    parser.add_argument("--pkg", help="input the package name or the file which contains packages")
    parser.add_argument("--release", help="input the release")
    args = parser.parse_args()
    if not args.project:
        print("Please input the project which to build")
        print("========================================")
        parser.print_help()
        exit(1)
    context.project = args.project
    context.branch = args.branch or 'master'
    context.type = args.type
    context.rootdir = args.rootdir or os.getcwd()
    context.os = args.os or os.environ.get("DISTRO", "centos")
    context.mirror = args.mirror or None
    if not context.os:
        print("input your operating system")
        exit(1)

    if not context.mirror:
        print("input your local mirror repo address")
        exit(1)

    context.package = args.pkg

    context.project_name = os.path.splitext(os.path.basename(args.project))[0]
    context.workdir = os.path.abspath(os.path.join(context.rootdir, context.os, args.type))
    context.TIS_DIST = ".stx"
    context.logfile = os.path.join(context.rootdir, 'logs', "%s.log" % time.strftime("%y-%m-%d", time.localtime()))
    context.platform_release = args.release or time.strftime("%y.%m", time.localtime())


def fetch_project(ctxt):
    if re.match(r'(?:http|ftp)s?://', ctxt.project, re.I):
        dirname = os.path.basename(ctxt.project)
        shell.git_checkout(ctxt.project, dist_dir=os.path.join(ctxt.rootdir, 'projects', dirname))
        ctxt.project = os.path.join(ctxt.rootdir, 'projects', dirname)
    if not os.path.isdir(ctxt.project):
        raise Exception('Project %s not Exist' % ctxt.project)


def main():
    ctxt = Context()
    prepare_context(ctxt)

    logger.init(ctxt.logfile)
    log = logger.getLogger('main')
    log.info("Start to build project %s" % ctxt.project_name)

    fetch_project(ctxt)

    manager.execute(ctxt)


