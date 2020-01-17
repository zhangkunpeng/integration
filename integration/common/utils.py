import os, shutil
from integration.common import log


def copy(src, dist):
    log.debug("Copy From %s to %s" % (src, dist))
    if os.path.isfile(src):
        shutil.copy2(src, dist)
    elif os.path.isdir(src):
        for name in os.listdir(src):
            fullpath = os.path.join(src, name)
            if os.path.isdir(fullpath):
                shutil.copytree(fullpath, os.path.join(dist, name))
            elif os.path.isfile(fullpath):
                shutil.copy2(fullpath, dist)
    else:
        log.error("Copy Failed. src path %s is not exist" % src)


def find_files(d, suffix):
    files = []
    for root, dirs, filenames in os.walk(d):
        files.extend([ os.path.join(root, f) for f in filenames if f.endswith(suffix)])
    if files:
        log.info("Find out %s files: %s" % (suffix, files))
    return files


def find_out_files(d, suffix):
    files = find_files(d, suffix)
    if not files:
        log.error("Can not find out '%s' files in %s" % (suffix, d))
    return files