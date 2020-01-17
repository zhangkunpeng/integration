from integration.build import shell
from integration.common import exception
rpm = "/usr/bin/rpm"
rpmbuild = "/usr/bin/rpmbuild"


def srpm_extract(srpmfile, topdir):
    # rpm -i --nosignature --root=$ROOT_DIR --define="%_topdir $BUILD_DIR" $ORIG_SRPM_PATH 2>> /dev/null
    cmd = [rpm, "-i", "--nosignature", "--define=%%_topdir %s" % topdir, srpmfile]
    ret = shell.popen_communicate(cmd)
    if ret != 0:
        raise exception.CriticalException('Extract %s Failed!', srpmfile)


def build_srpm(specfile, topdir=None, **kwargs):
    cmd = [rpmbuild, '-bs', specfile, '--undefine=dist']
    if topdir:
        cmd.append('--define=%%_topdir %s' % topdir)
    for k, v in kwargs.items():
        cmd.append('--define=\'%s %s\'' % (k, v))
    ret = shell.popen_communicate(cmd)
    if ret != 0:
        raise exception.CriticalException('BUILD SRPM Failed!')
    # sed -i -e "1 i%define _tis_build_type $BUILD_TYPE" $SPEC_PATH
    # sed -i -e "1 i%define tis_patch_ver $TIS_PATCH_VER" $SPEC_PATH


def query_srpm_tag(srpmfile, tag):
    cmd = [rpm,"-qp", "--queryformat=%%{%s}" % tag.upper(), "--nosignature", srpmfile]
    return shell.check_output(cmd)

