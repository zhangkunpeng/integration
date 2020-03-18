from build import shell, logger

log = logger.getLogger("RPMBUILD")

rpm = "/usr/bin/rpm"
rpmbuild = "/usr/bin/rpmbuild"
rpmspec = "/usr/bin/rpmspec"
yumbuilddep = "/usr/bin/yum-builddep"
createrepo = "/usr/bin/createrepo"
yum = "/usr/bin/yum"
yumconf = "/etc/yum.conf"


def srpm_extract(srpmfile, topdir):
    # rpm -i --nosignature --root=$ROOT_DIR --define="%_topdir $BUILD_DIR" $ORIG_SRPM_PATH 2>> /dev/null
    cmd = [rpm, "-i", "--nosignature", "--define=%%_topdir %s" % topdir, srpmfile]
    ret = shell.popen_communicate(cmd)
    if ret != 0:
        raise Exception('Extract %s Failed!', srpmfile)


def build_srpm(specfile, topdir=None, **kwargs):
    cmd = [rpmbuild, '-bs', specfile, '--undefine=dist']
    if topdir:
        cmd.append('--define=%%_topdir %s' % topdir)

    lines = []
    with open(specfile, 'r', encoding='utf-8') as f:
        for l in f:
            lines.append(l)
    for k, v in kwargs.items():
        lines.insert(0, "%%define %s %s\n" % (k, v))
    with open(specfile, 'w', encoding='utf-8') as f:
        f.write(''.join(lines))
    ret = shell.popen_communicate(cmd)
    if ret != 0:
        raise Exception('BUILD SRPM Failed!')
    # sed -i -e "1 i%define _tis_build_type $BUILD_TYPE" $SPEC_PATH
    # sed -i -e "1 i%define tis_patch_ver $TIS_PATCH_VER" $SPEC_PATH


def query_srpm_tag(srpmfile, tag):
    cmd = [rpm,"-qp", "--queryformat=%%{%s}" % tag.upper(), "--nosignature", srpmfile]
    return shell.check_output(cmd)


def build_rpm(srpm_file, topdir):
    log.info("##### BUILD RPM - %s" % srpm_file)
    cmd = [" ".join([rpmbuild, "-bb", srpm_file, "--define='%%_topdir %s'" % topdir])]
    ret = shell.popen_communicate(cmd)
    if ret == 0:
        log.info("BUILD SUCCESS")
    else:
        log.warning("BUILD FAILED")


def install_build_dependence(srpmfile):
    cmd = [yumbuilddep, "-c", yumconf, "-y", srpmfile]
    shell.check_call(cmd, stdout=-1)


def install_rpm(rpmfile):
    cmd = [yumbuilddep, "-c", yumconf, "-y", rpmfile]
    shell.check_call(cmd)


def update_repodata(repopath):
    cmd = [createrepo, "--update", repopath]
    shell.check_call(cmd, stdout=-1)


def yum_clean_cache():
    cmd = [yum,"-c", yumconf, "clean", "all"]
    shell.check_call(cmd)


def yum_makecache():
    cmd = [yum,"-c", yumconf, "makecache"]
    shell.check_call(cmd)


def yum_install(package):
    cmd = [yum,"-c", yumconf, "install", "-y", package]
    shell.check_call(cmd)