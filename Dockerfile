# In case of insufficient resources on OpenShift,
# check https://bbpteam.epfl.ch/project/spaces/display/INFRA/OpenShift#OpenShift-OpenShiftbuildsexitswitherrorcode137.

FROM ubuntu
WORKDIR /app

RUN apt update && apt  -y install openssh-client make python-pip git \
bash python-dev gcc libc-dev libnss-wrapper gettext-base vim iputils-ping telnet
#TO REMOVE?
ENV DEBIAN_FRONTEND=noninteractive
RUN apt install -y tzdata  && ln -fs /usr/share/zoneinfo/Europe/Zurich /etc/localtime && dpkg-reconfigure --frontend noninteractive tzdata \
 && useradd -g 0 -ms /bin/bash bbpvizsoa 

# ENV LD_PRELOAD=libnss_wrapper.so
ENV LD_PRELOAD=/usr/lib/libnss_wrapper.so
ENV NSS_WRAPPER_PASSWD=/app/passwd
ENV NSS_WRAPPER_GROUP=/app/group
ENV DOCKER_FILES=./rendering_resource_manager_service/deployment/openshift

ADD . /app

COPY $DOCKER_FILES/passwd.template  $DOCKER_FILES/group $DOCKER_FILES/gunicorn.sh  /app/
COPY $DOCKER_FILES/local_settings.py /app/rendering_resource_manager_service/ 

RUN mkdir /.ssh \
 &&  chmod 700 /.ssh \
 && chmod 777 /app/  \
 && mkdir /var/tmp/django_cache \
 && touch /app/passwd && chmod 777 /app/passwd \
 && pip install virtualenv  \
 && /usr/bin/make virtualenv \
 && bash -c "source platform_venv/bin/activate && pip install -r requirements.txt" \
 && chmod 770 gunicorn.sh
 
EXPOSE 8383
#USER bbpvizsoa
CMD ./gunicorn.sh
