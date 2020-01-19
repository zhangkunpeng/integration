FROM centos:7

ENV DISTRO="centos", SYSTEM="starlingx"
RUN yum install -y epel-release git rpm-build rpm-sign make createrepo gcc && \
    yum install -y python3-pip mock \
                   python36-yaml \
                   python36-psutil

ADD . /integration

WORKDIR /integration

RUN python3 setup.py install

CMD /usr/sbin/init