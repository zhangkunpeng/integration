import os
import shutil
import subprocess

from integration.common import log

patch = "/usr/bin/patch"
git = "/usr/bin/git"


def check_call(cmd, **kwargs):
    msg = "\n%s\n%s\n......\n" % ("".ljust(100, "*"), " ".join(cmd))
    log.info(msg)
    if kwargs.get("stdoutfile"):
        with open(kwargs.get("stdoutfile"), 'a') as f:
            f.write(msg)
            f.flush()
            kwargs.pop("stdoutfile")
            if "stdout" not in kwargs:
                kwargs["stdout"] = f
            if "stderr" not in kwargs:
                kwargs["stderr"] = f
    return subprocess.check_call(cmd, **kwargs)


def check_output(cmd, **kwargs):
    msg = "\n%s\n%s\n......\n" % ("".ljust(100, "*"), " ".join(cmd))
    log.info(msg)
    ret = subprocess.check_output(cmd, **kwargs).decode("UTF-8").strip()
    log.info("Result %s", ret)
    return ret


def popen_communicate(cmd, input=None, timeout=None, **kwargs):
    log.info("\n%s\n%s\n......\n" % ("".ljust(100, "*"), " ".join(cmd)))
    ret = subprocess.Popen(cmd, **kwargs)
    out, err = ret.communicate(input=input, timeout=timeout)
    log.info("Return Code: %s", ret.returncode)
    if out and type(out) == bytes:
        log.debug(out.decode("utf-8"))
    if err and type(err) == bytes:
        log.error(err.decode("utf-8"))
    return ret.returncode


def patch_apply(patchfile, cwd):
    if not os.path.isfile(patchfile):
        return
    log.info("apply patch: %s" % patchfile)
    #patch -f $PATCH_ARGS --no-backup-if-mismatch < $PATCH
    #cmd = [patch, '-f', '-p1', '--no-backup-if-mismatch', '<', patchfile]
    cmd = ["%s -f -p1 --no-backup-if-mismatch < %s" % (patch, patchfile)]
    return check_call(cmd, cwd=cwd, shell=True)


def echo_env(envfile, env, key):
    cmd = ["source %s && echo $%s" % (envfile, key)]
    return check_output(cmd, env=env, shell=True)


def fetch_all_params(envfile, env):
    params = {}
    with open(envfile, 'r') as f:
        for line in f.readlines():
            if "=" in line:
                key = line[:line.rfind('=')]
                params[key] = None
    for key in params.keys():
        params[key] = echo_env(envfile, env, key)
    return params


# git command
def git_checkout(url, dist_dir, branch='master'):
    log.info("fetch repo: %s branch: %s in dir: %s" % (url, branch, dist_dir))
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
    return check_call([git, "clone", "--depth=1", "--branch=%s" % branch, url, dist_dir])


def git_commit_count(repodir, commit_id):
    cmd = [git, "rev-list", "--count", "%s..HEAD" % commit_id]
    output = check_output(cmd, cwd=repodir)
    return int(output) if output else 0


def git_plus_by_status(repodir):
    cmd = [git, "status", "--porcelain"]
    output = check_output(cmd, cwd=repodir)
    return 1 if output else 0

