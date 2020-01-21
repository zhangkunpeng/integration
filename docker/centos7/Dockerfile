FROM centos:7

ENV DISTRO="centos"
ENV SYSTEM="starlingx"
RUN yum install -y epel-release git rpm-build rpm-sign make createrepo gcc && \
    yum install -y python3-pip mock \
                   python36-yaml \
                   python36-psutil

RUN groupadd -g 751 cgts && \
    echo "mock:x:751:root" >> /etc/group && \
#    echo "mockbuild:x:9001:" >> /etc/group && \
#    useradd -s /sbin/nologin -u 9001 -g 9001 mockbuild && \
    useradd -r -g cgts -m starlingx
    echo "config_opts['use_nspawn'] = False" >> /etc/mock/site-defaults.cfg && \
    echo "config_opts['rpmbuild_networking'] = True" >> /etc/mock/site-defaults.cfg && \
    echo  >> /etc/mock/site-defaults.cfg

COPY docker/centos7/starlingx.cfg /etc/mock/starlingx.cfg

ADD . /integration

WORKDIR /integration

RUN python3 setup.py install

USER starlingx

CMD /usr/sbin/init