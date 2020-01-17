
starlingx = {
    'comps.xml': '''
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE comps PUBLIC "-//Red Hat, Inc.//DTD Comps info//EN" "comps.dtd">
<comps>
  <group>
    <id>buildsys-build</id>
    <name>Buildsystem building group</name>
    <description/>
    <default>false</default>
    <uservisible>false</uservisible>
    <packagelist>
      <packagereq type="mandatory">bash</packagereq>
      <packagereq type="mandatory">bzip2</packagereq>
      <packagereq type="mandatory">coreutils</packagereq>
      <packagereq type="mandatory">cpio</packagereq>
      <packagereq type="mandatory">diffutils</packagereq>
      <packagereq type="mandatory">epel-release</packagereq>
      <packagereq type="mandatory">epel-rpm-macros</packagereq>
      <packagereq type="mandatory">findutils</packagereq>
      <packagereq type="mandatory">gawk</packagereq>
      <packagereq type="mandatory">gcc</packagereq>
      <packagereq type="mandatory">gcc-c++</packagereq>
      <packagereq type="mandatory">grep</packagereq>
      <packagereq type="mandatory">gzip</packagereq>
      <packagereq type="mandatory">hostname</packagereq>
      <packagereq type="mandatory">info</packagereq>
      <packagereq type="mandatory">make</packagereq>
      <packagereq type="mandatory">patch</packagereq>
      <packagereq type="mandatory">redhat-rpm-config</packagereq>
      <packagereq type="mandatory">rpm-build</packagereq>
      <packagereq type="mandatory">sed</packagereq>
      <packagereq type="mandatory">shadow-utils</packagereq>
      <packagereq type="mandatory">tar</packagereq>
      <packagereq type="mandatory">unzip</packagereq>
      <packagereq type="mandatory">util-linux-ng</packagereq>
      <packagereq type="mandatory">which</packagereq>
      <packagereq type="mandatory">xz</packagereq>
    </packagelist>
  </group>
</comps>
    ''',
    'mock.cfg': '''
config_opts['root'] = 'BUILD_ENV/mock'
config_opts['target_arch'] = 'x86_64'
config_opts['legal_host_arches'] = ('x86_64',)
config_opts['chroot_setup_cmd'] = 'install @buildsys-build'
config_opts['dist'] = 'el7'  # only useful for --resultdir variable subst
config_opts['releasever'] = '7'
config_opts['rpmbuild_networking'] = False

config_opts['yum.conf'] = """
[main]
keepcache=1
debuglevel=2
reposdir=/dev/null
logfile=/var/log/yum.log
retries=20
obsoletes=1
gpgcheck=0
assumeyes=1
syslog_ident=mock
syslog_device=

# repos
[local-std]
name=local-std
baseurl=LOCAL_BASE/MY_BUILD_DIR/std/rpmbuild/RPMS
enabled=1
skip_if_unavailable=1
metadata_expire=0

[local-rt]
name=local-rt
baseurl=LOCAL_BASE/MY_BUILD_DIR/rt/rpmbuild/RPMS
enabled=1
skip_if_unavailable=1
metadata_expire=0

[local-installer]
name=local-installer
baseurl=LOCAL_BASE/MY_BUILD_DIR/installer/rpmbuild/RPMS
enabled=1
skip_if_unavailable=1
metadata_expire=0

[TisCentos7Distro]
name=Tis-Centos-7-Distro
enabled=1
baseurl=LOCAL_BASE/MY_REPO_DIR/cgcs-centos-repo/Binary
failovermethod=priority
exclude=kernel-devel libvirt-devel


"""
    '''
}