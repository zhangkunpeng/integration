FROM centos:7

ENV DISTRO="centos"
ENV SYSTEM="starlingx"
RUN yum install -y epel-release git rpm-build rpm-sign make createrepo gcc && \
    yum install -y python3-pip mock \
                   python36-yaml \
                   python36-psutil

RUN useradd -s /sbin/nologin -u 9001 -g 9001 mockbuild

COPY docker/centos7/starlingx.cfg /etc/mock/starlingx.cfg

ADD . /integration

WORKDIR /integration

RUN python3 setup.py install

CMD /usr/sbin/init