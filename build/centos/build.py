import json
import os
from build import logger, shell, utils
from build.centos import rpmutil
from build.context import Context

log = logger.getLogger("BUILD")


class CentosBuild(object):

    def __init__(self, ctxt, package):
        self.name = os.path.basename(package)
        self.package = package
        self.abspath = os.path.join(ctxt.project, package)
        self.distro_dir = os.path.join(ctxt.project, package, ctxt.os)
        self.distro_repo = os.path.join(ctxt.mirror, "cgcs-centos-repo/Source/bashXXXXX.src.rpm")
        self.third_party = os.path.join(ctxt.mirror, "cgcs-3rd-party-repo")
        self.env = Context({
            'FILES_BASE': "%s/files" % ctxt.os,
            'CGCS_BASE': self.distro_repo,
            'PKG_BASE': self.abspath,
            'STX_BASE': self.distro_repo,
            'PATCHES_BASE': "%s/patches" % ctxt.os,
            'DISTRO': ctxt.os,
            'TIS_DIST': ctxt.TIS_DIST
        })
        self.workdir = os.path.join(ctxt.workdir, self.name)
        self.srpmbuild_dir = os.path.join(self.workdir, "srpmbuild")
        self.build_spec_dir = os.path.join(self.srpmbuild_dir, 'SPECS')
        self.build_srpm_dir = os.path.join(self.srpmbuild_dir, 'SRPMS')
        self.build_rpm_dir = os.path.join(self.srpmbuild_dir, 'RPMS')
        self.build_src_dir = os.path.join(self.srpmbuild_dir, 'SOURCES')
        self.original_file = None
        self.srpm_file = None
        self.rpm_files = None
        self.version = None
        self.release = None
        self.success = False
        self.platform_release = ctxt.release
        self.type = ctxt.type

    def update_context(self):
        log.info(json.dumps(self.__dict__))

    def build_srpm(self):
        self.find_build_mode()
        self.find_build_data()

        utils.clean_dir(self.srpmbuild_dir)
        utils.makedirs(self.build_spec_dir, self.build_src_dir)

        if self.original_file.endswith('.src.rpm'):
            rpmutil.srpm_extract(self.original_file, self.srpmbuild_dir)
        if self.original_file.endswith('.spec'):
            utils.copy(self.original_file, self.build_spec_dir)
        self.__copy_additional_src()
        self.__apply_meta_patches()
        specfiles = utils.find_out_files(self.build_spec_dir, '.spec')
        log.info("##### BUILD SRPM - %s" % self.name)
        defines = {
            '_tis_build_type': self.type,
            'tis_patch_ver': self.env.TIS_PATCH_VER,
            'platform_release': self.platform_release,
            '_tis_dist': self.env.TIS_DIST,
        }
        rpmutil.build_srpm(specfiles[0], topdir=self.srpmbuild_dir, **defines)
        self.srpm_file = utils.find_out_files(self.build_srpm_dir, ".src.rpm")[0]
        self.name = rpmutil.query_srpm_tag(self.srpm_file, 'Name')
        self.version = rpmutil.query_srpm_tag(self.srpm_file, 'Version')
        self.release = rpmutil.query_srpm_tag(self.srpm_file, 'Release')
        self.update_context()

    def find_build_mode(self):
        srpm_path = os.path.join(self.distro_dir, "srpm_path")

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
            log.error("Invalid srpm path '%s', evaluated as '%s', found in '%s'" % (line, filepath, srpm_path))

        if os.path.exists(srpm_path):
            with open(srpm_path) as f:
                for line in f.readlines():
                    line = line.strip()
                    if line and line.endswith('.src.rpm'):
                        self.original_file = orig_srpm_path(line)

        spec_path = self.distro_dir
        for filename in os.listdir(spec_path):
            if filename.endswith(".spec"):
                self.original_file = os.path.join(spec_path, filename)
        if not self.original_file:
            log.error("Please provide only one of srpm_path or .spec files, not None, in '%s'" % spec_path)

    def find_build_data(self):
        build_srpm_data = os.path.join(self.distro_dir, "build_srpm.data")
        if not os.path.exists(build_srpm_data):
            log.error("%s not found" % build_srpm_data)
        self.env.update(shell.fetch_all_params(build_srpm_data, self.env))
        if not self.env.TIS_PATCH_VER:
            log.error("TIS_PATCH_VER must be set in %s", build_srpm_data)
        if self.env.TIS_PATCH_VER.startswith("GITREVCOUNT"):
            if not self.env.TIS_BASE_SRCREV:
                log.error("TIS_BASE_SRCREV must be set in %s", build_srpm_data)
            items = self.env.TIS_PATCH_VER.split("+")
            count = 0 if len(items) == 1 else int(items[1]) + \
                                              shell.git_commit_count(self.abspath, self.env.TIS_BASE_SRCREV) + \
                                              shell.git_plus_by_status(self.abspath)
            self.env.TIS_PATCH_VER = str(count)

    def __copy_additional_src(self):
        """
        复制额外的source 和patches 到 rpmbuild/SOURCES
        example:
           files/*
           centos/files/*
           ${CGCS_BASE}/downloads/XXXX.tar.gz

           centos/patches
        """
        if self.env.COPY_LIST:
            copy_path_list = self.env.COPY_LIST.split(' ')
            log.debug('COPY_LIST: %s', copy_path_list)
            for p in copy_path_list:
                p = p[:-2] if p.endswith("/*") else p
                p = p if os.path.isabs(p) else os.path.join(self.abspath, p)
                utils.copy(p, self.build_src_dir)
        patches_dir = os.path.join(self.distro_dir, "patches")
        if os.path.exists(patches_dir):
            log.info('copy additional patches from DIR: %s', patches_dir)
            utils.copy(patches_dir, self.build_src_dir)

    def __apply_meta_patches(self):
        meta_patch_dir = os.path.join(self.distro_dir, "meta_patches")
        if os.path.exists(meta_patch_dir):
            log.info('apply meta patches. DIR: %s', meta_patch_dir)
            meta_patch_order = os.path.join(meta_patch_dir, "PATCH_ORDER")
            with open(meta_patch_order) as f:
                for line in f.readlines():
                    patchfile = os.path.join(meta_patch_dir, line.strip())
                    shell.patch_apply(patchfile, cwd=self.srpmbuild_dir)

    def build_rpm(self):
        rpmutil.install_build_dependence(self.srpm_file)
        rpmutil.build_rpm(self.srpm_file, self.srpmbuild_dir)

        self.rpm_files = utils.find_out_files(self.build_rpm_dir, ".rpm")
        self.success = True
        self.update_context()


