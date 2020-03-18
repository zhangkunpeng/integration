import argparse
import os, yaml
from integration.build import manager
from integration.common import log

fields = [
    ('source',  'input the source which to build, dir or git repo is required'),
    ('branch',  'the git repo branch'),
    ('type',    'build type'),
    ('rootdir', 'input the root dir'),
    ('output',  'input the output repo dir'),
    ('mirror',  'input the mirror path'),
    ('release', 'input the release'),
    ('postfix', 'input the postfix'),
    ('system',  'input the system name'),
    ('os',      'input the os system'),
]


def inspect_arguments(ctxt):
    none_keys = []
    for k, h in fields:
        if not ctxt[k]:
            none_keys.append(k)
    if none_keys:
        raise Exception('Arguments %s must be input' % none_keys)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', help='input args from file')
    for k, h in fields:
        parser.add_argument('--%s' % k, help=h)
    parser.add_argument("-p", "--package", help="input the build package")
    parser.add_argument("-w", "--worker", help="input the build worker number", default=2)
    args = parser.parse_args()

    if args.file:
        if not os.path.isfile(args.file):
            print('file %s is not existed' % args.file)
            exit(1)
        with open(args.file, 'r', encoding='utf-8') as f:
            args.__dict__.update(yaml.load(f.read()))
    inspect_arguments(args.__dict__)
    log.CONFIG(os.path.join(args.rootdir, 'build-%s-%s.log' % (args.system, args.type)))
    logger = log.getLogger('main', std=True)
    logger.info('Init')
    manager.init(args.__dict__)

