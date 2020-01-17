from integration.common.context import Context
from integration.common import log
import os
import argparse
import yaml

env = Context()

# __ENV__ = ['DISTRO', 'RELEASE', 'MIRROR', 'SYSTEM', 'type', 'source', 'rootdir']
#
# for e in __ENV__:
#     if os.environ.get(e) is None:
#         log.critical('Environment %s must be set', e)
#     env[e.lower()] = os.environ.get(e)


def prepare_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', help='input args from file')
    parser.add_argument("--source", help="input the source which to build, dir or git repo is required")
    parser.add_argument("--branch", help="the git repo branch")
    parser.add_argument("--type", help="build type", choices=["std", "rt"], default="std")
    parser.add_argument("--rootdir", help="input the work dir")
    parser.add_argument("--output", help="input the output repo dir")
    parser.add_argument("--distro", help="input the OS name")
    parser.add_argument("--mirror", help="input the mirror path")
    parser.add_argument("--release", help="input the release")
    parser.add_argument("--postfix", help="input the postfix", default='stx')
    parser.add_argument("-p", "--pkg", help="input the build pkg")
    args = parser.parse_args()

    if args.file:
        if not os.path.isfile(args.file):
            log.critical('file %s is not existed', args.file)
        with open(args.file, 'r', encoding='utf-8') as f:
            args.__dict__.update(yaml.load(f.read()))
        del args['file']
    return args.__dict__
