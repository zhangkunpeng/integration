from integration.build import prepare_arguments, env, build
import os
from integration.common import log
from integration.build import build

__ENV__ = ['DISTRO', 'SYSTEM']
keys = __ENV__ + ['source', 'type', 'rootdir', 'postfix', 'mirror', 'release', 'output']


def exec(source, type, rootdir, postfix='stx', **kwargs):
    env.source = source
    env.type = type
    env.rootdir = rootdir
    env.postfix = postfix
    env.update(kwargs)

    for e in __ENV__:
        if e not in env and env[e] is None:
            env[e] = os.environ.get(e)

    unknown_args = [e for e in keys if e not in env or env[e] is None]
    if unknown_args:
        log.critical('Argument %s must be input', unknown_args)
    if env.pkg:
        env.pkglist = [env.pkg]
    env.max_workers = 4

    chain = build.BuildChain(**env)
    chain.fetch_source()
    chain.fetch_package_list()
    chain.build_iteration()


def main():
    args = prepare_arguments()
    exec(**args)
