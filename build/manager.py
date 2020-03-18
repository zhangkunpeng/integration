import json
import os
from build import logger

from build.centos.build import CentosBuild
from build.context import Context

log = logger.getLogger("MANAGER")


def build_package_list(ctxt):
    if ctxt.package:
        relpath = os.path.join(ctxt.project, ctxt.package)
        if os.path.isfile(relpath):
            with open(relpath, 'r') as f:
                plist = [n.strip() for n in f.readlines() if n.strip()]
                return plist
        if os.path.isdir(relpath):
            return [ctxt.package]
        raise Exception("package %s was not found in source" % ctxt.package)
    else:
        raise Exception("package is empty or None")


def execute(ctxt):
    packages = build_package_list(ctxt)
    ctxt.build = Context()
    result = {}
    for package in packages:
        build = CentosBuild(ctxt, package)
        build.build_srpm()
        build.build_rpm()
        result[package] = build.success
        if not build.success:
            log.error("build failed")
            break
        ctxt.build[build.name] = build

    log.info(json.dumps(result, indent=4))
