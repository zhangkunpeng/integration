__all__ = ['rpmutil', 'CentosBuild', 'mock']

from integration.build import BaseBuild, Builder
from integration.build import shell
from integration.build.api import env
from integration.common import log, utils
from integration.build.centos import mock, rpmutil
import os
import subprocess
import shutil

mocks = []


class CentosBuild(BaseBuild):

    DISTRO = "centos"

    def __init__(self, pkg, **kwargs):
        super(CentosBuild, self).__init__(pkg, **kwargs)
        self.distro_repo = os.path.join(env.mirror, "cgcs-centos-repo")
        self.third_party = os.path.join(env.mirror, "cgcs-3rd-party-repo")
        self.TIS_DIST = '.%s' % env.postfix
        self.srpmbuild_dir = os.path.join(self.workdir, "srpmbuild", self.name)
        self.localrepo = os.path.join(self.workdir, "repo")
        if not os.path.exists(self.localrepo):
            os.makedirs(self.localrepo, mode=0o755)
        self.mock = self.build_mock()

        self.original_file = None
        self.srpm_file = None
        self.build_spec_dir = os.path.join(self.srpmbuild_dir, 'SPECS')
        self.build_srpm_dir = os.path.join(self.srpmbuild_dir, 'SRPMS')
        self.build_rpm_dir = os.path.join(self.srpmbuild_dir, 'RPMS')
        self.build_src_dir = os.path.join(self.srpmbuild_dir, 'SOURCES')
        self.mkdirs(self.build_spec_dir, self.build_src_dir)

    def build_mock(self):
        for m in mocks:
            if self.index == m.index:
                return m
        m = mock.Mock(self.index, workdir=self.workdir, local_repo=self.localrepo)
        mocks.append(m)
        return m

    def do_build(self):
        super(CentosBuild, self).do_build()

    def cleanup(self):
        log.info('Clean Build Environment')
        for dirname in [self.build_srpm_dir, self.build_rpm_dir]:
            if os.path.exists(dirname):
                shutil.rmtree(dirname)

    def prepare_source(self):
        if self.srpm_file is None:
            self.find_build_original()
            self.find_build_data()
            self.build_srpm()
        log.info('SRPM build success: %s', self.srpm_file)

    def compile(self):
        self.rpmbuild_dir = os.path.join(self.localrepo, self.fullname())
        self.mkdirs(self.rpmbuild_dir)
        defines = {
            '_tis_dist': self.TIS_DIST,
            'platform_release': env.release
        }
        ret = self.mock.execute(self.srpm_file, result_dir=self.rpmbuild_dir, defines=defines)
        if ret != 0:
            self.mark_fail()
        else:
            self.mark_success()
        exit(1 if ret else 0)

    def update_repo(self, max_workers=1):
        cmd = ['/usr/bin/createrepo_c']
        if os.path.exists(os.path.join(self.LOCAL_REPO_DIR, '/repodata/repomd.xml')):
            cmd.extend(['--update', '--retain-old-md', "%d" % max_workers])
        cmd.extend(["--workers", "%d" % max_workers, self.LOCAL_REPO_DIR])
        subprocess.check_call(cmd, stdout=subprocess.PIPE)

    # build in starlingx
    def find_build_original(self):

        def orig_srpm_path(line):
            if line.startswith("/"):
                filepath = line
            elif line.startswith("repo:"):
                # TODO 暂时未发现repo，遇到后再补充
                filepath = line.replace("repo:stx", self.distro_repo, 1)
            elif line.startswith("3rd_party:"):
                filepath = line.replace("3rd_party:", self.third_party + "/", 1)
            elif line.startswith("mirror:"):
                filepath = line.replace("mirror:", self.distro_repo + "/", 1) \
                    .replace("CentOS/tis-r3-CentOS/kilo/", "") \
                    .replace("CentOS/tis-r3-CentOS/mitaka/", "")
            else:
                filepath = self.distro_repo + "/" + line
            if os.path.exists(filepath):
                return filepath
            log.error("Invalid srpm path '%s', evaluated as '%s', found in '%s'", line, filepath, srpm_path)

        srpm_path = os.path.join(self.pkgdir, "%s/srpm_path" % self.DISTRO)
        if os.path.exists(srpm_path):
            with open(srpm_path) as f:
                for line in f.readlines():
                    line = line.strip()
                    if line and line.endswith('.src.rpm'):
                        self.original_file = orig_srpm_path(line)

        spec_path = os.path.join(self.pkgdir, self.DISTRO)
        for filename in os.listdir(spec_path):
            if filename.endswith(".spec"):
                self.original_file = os.path.join(spec_path, filename)
        if not self.original_file:
            log.error("Please provide only one of srpm_path or .spec files, not None, in '%s'" % spec_path)

    def find_build_data(self, build_srpm_data_file=None):
        if build_srpm_data_file is None:
            build_srpm_data_file = os.path.join(self.pkgdir, "%s/build_srpm.data" % self.DISTRO)
        if not os.path.exists(build_srpm_data_file):
            log.error("%s not found", build_srpm_data_file)
        stx_env = {
            'FILES_BASE': "%s/files" % self.DISTRO,
            'CGCS_BASE': self.distro_repo,
            'PKG_BASE': self.pkgdir,
            'STX_BASE': self.distro_repo,
            'PATCHES_BASE': "%s/patches" % self.DISTRO,
            'DISTRO': self.DISTRO
        }
        self.__dict__.update(shell.fetch_all_params(build_srpm_data_file, stx_env))
        if not self.TIS_PATCH_VER:
            log.error("TIS_PATCH_VER must be set in %s", build_srpm_data_file)
        if self.TIS_PATCH_VER.startswith("GITREVCOUNT"):
            if not self.TIS_BASE_SRCREV:
                log.error("TIS_BASE_SRCREV must be set in %s", build_srpm_data_file)
            items = self.TIS_PATCH_VER.split("+")
            count = 0 if len(items) == 1 else int(items[1]) + \
                                              shell.git_commit_count(self.pkgdir, self.TIS_BASE_SRCREV) + \
                                              shell.git_plus_by_status(self.pkgdir)
            self.TIS_PATCH_VER = str(count)

    def build_srpm(self):
        if self.original_file.endswith('.src.rpm'):
            rpmutil.srpm_extract(self.original_file, self.build_dir)
        if self.original_file.endswith('.spec'):
            utils.copy(self.original_file, self.build_spec_dir)
        self.__copy_additional_src()
        self.__apply_meta_patches()
        specfiles = utils.find_out_files(self.build_spec_dir, '.spec')
        log.info("##### BUILD SRPM - %s" % self.name)
        defines = {
            '_tis_build_type': env.type,
            'tis_patch_ver': self.TIS_PATCH_VER,
            'platform_release': env.release,
            '_tis_dist': self.TIS_DIST
        }
        rpmutil.build_srpm(specfiles[0], topdir=self.build_dir, **defines)
        self.srpm_file = utils.find_out_files(self.build_srpm_dir, ".src.rpm")[0]
        self.name = rpmutil.query_srpm_tag(self.srpm_file, 'Name')
        self.version = rpmutil.query_srpm_tag(self.srpm_file, 'Version')
        self.release = rpmutil.query_srpm_tag(self.srpm_file, 'Release')

    def __copy_additional_src(self):
        """
        复制额外的source 和patches 到 rpmbuild/SOURCES
        example:
           files/*
           centos/files/*
           ${CGCS_BASE}/downloads/XXXX.tar.gz

           centos/patches
        """
        if 'COPY_LIST' in self.__dict__:
            copy_path_list = self.COPY_LIST.split(' ')
            log.debug('COPY_LIST: %s', copy_path_list)
            for p in copy_path_list:
                p = p[:-2] if p.endswith("/*") else p
                p = p if os.path.isabs(p) else os.path.join(self.pkgdir, p)
                utils.copy(p, self.build_src_dir)
        patches_dir = os.path.join(self.pkgdir, "%s/patches" % self.DISTRO)
        if os.path.exists(patches_dir):
            log.info('copy additional patches from DIR: %s', patches_dir)
            utils.copy(patches_dir, self.build_src_dir)

    def __apply_meta_patches(self):
        meta_patch_dir = os.path.join(self.pkgdir, "%s/meta_patches" % self.DISTRO)
        if os.path.exists(meta_patch_dir):
            log.info('apply meta patches. DIR: %s', meta_patch_dir)
            meta_patch_order = os.path.join(meta_patch_dir, "PATCH_ORDER")
            with open(meta_patch_order) as f:
                for line in f.readlines():
                    patchfile = os.path.join(meta_patch_dir, line.strip())
                    shell.patch_apply(patchfile, cwd=self.build_dir)


class CentosBuilder(Builder):

    OS = 'centos'

    def __init__(self, *args, **kwargs):
        super(CentosBuilder, self).__init__(*args, **kwargs)
        self.srpmbuild_dir = os.path.join(self.workdir, "srpmbuild", self.name)
        self.localrepo = os.path.join(self.workdir, "repo")
        if not os.path.exists(self.localrepo):
            os.makedirs(self.localrepo, mode=0o755)

        self.distro_repo = os.path.join(env.mirror, "cgcs-centos-repo")
        self.third_party = os.path.join(env.mirror, "cgcs-3rd-party-repo")
        self.TIS_DIST = '.%s' % env.postfix

    def do_build(self, lock, ctxt):
        super(CentosBuilder, self).do_build(lock, ctxt)
        if self.success:
            return

    def build_srpm(self):
        pass

    def build_rpm(self):
        pass


    # StarlingX
    def find_build_original(self):
        original_file = None

        def orig_srpm_path(line):
            if line.startswith("/"):
                filepath = line
            elif line.startswith("repo:"):
                # TODO 暂时未发现repo，遇到后再补充
                filepath = line.replace("repo:stx", self.distro_repo, 1)
            elif line.startswith("3rd_party:"):
                filepath = line.replace("3rd_party:", self.third_party + "/", 1)
            elif line.startswith("mirror:"):
                filepath = line.replace("mirror:", self.distro_repo + "/", 1) \
                    .replace("CentOS/tis-r3-CentOS/kilo/", "") \
                    .replace("CentOS/tis-r3-CentOS/mitaka/", "")
            else:
                filepath = self.distro_repo + "/" + line
            if os.path.exists(filepath):
                return filepath
            log.error("Invalid srpm path '%s', evaluated as '%s', found in '%s'", line, filepath, srpm_path)

        srpm_path = os.path.join(self.pkgdir, "%s/srpm_path" % self.OS)
        if os.path.exists(srpm_path):
            with open(srpm_path) as f:
                for line in f.readlines():
                    line = line.strip()
                    if line and line.endswith('.src.rpm'):
                        original_file = orig_srpm_path(line)

        spec_path = os.path.join(self.pkgdir, self.OS)
        for filename in os.listdir(spec_path):
            if filename.endswith(".spec"):
                original_file = os.path.join(spec_path, filename)
        if not original_file:
            log.error("Please provide only one of srpm_path or .spec files, not None, in '%s'" % spec_path)
        return original_file

    def find_build_data(self, build_srpm_data_file=None):
        if build_srpm_data_file is None:
            build_srpm_data_file = os.path.join(self.pkgdir, "%s/build_srpm.data" % self.OS)
        if not os.path.exists(build_srpm_data_file):
            log.error("%s not found", build_srpm_data_file)
        stx_env = {
            'FILES_BASE': "%s/files" % self.OS,
            'CGCS_BASE': self.distro_repo,
            'PKG_BASE': self.pkgdir,
            'STX_BASE': self.distro_repo,
            'PATCHES_BASE': "%s/patches" % self.OS,
            'DISTRO': self.OS
        }
        self.__dict__.update(shell.fetch_all_params(build_srpm_data_file, stx_env))
        if not self.TIS_PATCH_VER:
            log.error("TIS_PATCH_VER must be set in %s", build_srpm_data_file)
        if self.TIS_PATCH_VER.startswith("GITREVCOUNT"):
            if not self.TIS_BASE_SRCREV:
                log.error("TIS_BASE_SRCREV must be set in %s", build_srpm_data_file)
            items = self.TIS_PATCH_VER.split("+")
            count = 0 if len(items) == 1 else int(items[1]) + \
                                              shell.git_commit_count(self.pkgdir, self.TIS_BASE_SRCREV) + \
                                              shell.git_plus_by_status(self.pkgdir)
            self.TIS_PATCH_VER = str(count)
