# https://github.com/robertdebock/docker-github-action-rpmbuild/blob/centos-7/Dockerfile
FROM centos:7

LABEL maintainer="Robert de Bock <robert@meinit.nl>"

WORKDIR /github/workspace

RUN yum install -y rpmdevtools yum-utils spectool python3 && \
    yum clean all && \
    rm -r -f /var/cache/*

CMD spectool --get-files --all SPECS/*.spec && \
    yum-builddep --assumeyes SPECS/*.spec && \
    rpmbuild --define "_topdir ${GITHUB_WORKSPACE}" -ba SPECS/*.spec
#    rpmbuild --define '_topdir /github/workspace' -ba SPECS/*.spec
