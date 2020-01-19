import argparse
import os
import yaml

from integration.build import env, build
from integration.common import log

_ENV = ['DISTRO', 'SYSTEM']
_fields = ['source', 'type', 'rootdir', 'postfix', 'mirror', 'release', 'output']


def execute():
    for e in _ENV:
        if e not in env or env[e] is None:
            env[e] = os.environ.get(e)

    unknown_args = [e for e in _ENV + _fields if e not in env or env[e] is None]
    if unknown_args:
        log.critical('Argument %s must be input', unknown_args)
    if env.pkg:
        env.pkglist = [env.pkg]
    env.max_workers = 4
    log.CONF('%s-%s' % (env.SYSTEM, env.DISTRO), logdir=env.rootdir)
    chain = build.BuildChain(**env)
    chain.fetch_source()
    chain.fetch_package_list()
    chain.build_iteration()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', help='input args from file')
    parser.add_argument("--source", help="input the source which to build, dir or git repo is required")
    parser.add_argument("--branch", help="the git repo branch")
    parser.add_argument("--type", help="build type", choices=["std", "rt"], default="std")
    parser.add_argument("--rootdir", help="input the work dir")
    parser.add_argument("--output", help="input the output repo dir")
    parser.add_argument("--mirror", help="input the mirror path")
    parser.add_argument("--release", help="input the release")
    parser.add_argument("--postfix", help="input the postfix", default='stx')
    parser.add_argument("-p", "--pkg", help="input the build pkg")
    args = parser.parse_args()

    if args.file:
        if not os.path.isfile(args.file):
            log.critical('file %s is not existed', args.file)
        with open(args.file, 'r', encoding='utf-8') as f:
            env.update(yaml.load(f.read()))
    env.update(args.__dict__)
    execute()


def run(source=None, type=None, rootdir=None, postfix='stx', **kwargs):
    env.source = source
    env.type = type
    env.rootdir = rootdir
    env.postfix = postfix
    env.update(kwargs)
    execute()
