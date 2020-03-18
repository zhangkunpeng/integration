FROM centos:7

ENV DISTRO=centos
ARG USER=starlingx
RUN yum install -y epel-release git rpm-build rpm-sign make createrepo gcc sudo && \
    yum install -y python3-pip mock \
                   python36-yaml \
                   python36-psutil

RUN useradd -d /home/$USER -g mock -m $USER && \
    echo '$USER  ALL=(ALL:ALL) NOPASSWD: ALL' >> /etc/sudoers && \
#    groupadd -g 751 cgts && \
#    echo "mock:x:751:root" >> /etc/group && \
#    echo "mockbuild:x:9001:" >> /etc/group && \
    useradd -s /sbin/nologin -g mock mockbuild && \
    echo "config_opts['use_nspawn'] = False" >> /etc/mock/site-defaults.cfg && \
    echo "config_opts['rpmbuild_networking'] = True" >> /etc/mock/site-defaults.cfg && \
    echo  >> /etc/mock/site-defaults.cfg

ADD . ./integration

RUN cd ./integration && sudo python3 setup.py install

#USER starlingx
#WORKDIR /home/starlingx

COPY docker/centos7/starlingx.cfg /etc/mock/starlingx.cfg


CMD /usr/sbin/init