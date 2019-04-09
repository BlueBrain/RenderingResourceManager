# In case of insufficient resources on OpenShift,
# check https://bbpteam.epfl.ch/project/spaces/display/INFRA/OpenShift#OpenShift-OpenShiftbuildsexitswitherrorcode137.

FROM ubuntu
WORKDIR /app

RUN apt update && apt  -y install openssh-client make python-pip git \
bash python-dev gcc libc-dev libnss-wrapper gettext-base vim iputils-ping telnet
#postgresql-dev && \

ENV DEBIAN_FRONTEND=noninteractive
RUN apt install -y tzdata  && ln -fs /usr/share/zoneinfo/Europe/Zurich /etc/localtime && dpkg-reconfigure --frontend noninteractive tzdata
ADD . /app

RUN useradd -g 0 -ms /bin/bash bbpvizsoa 

ENV LD_PRELOAD=libnss_wrapper.so
ENV NSS_WRAPPER_PASSWD=/app/passwd
ENV NSS_WRAPPER_GROUP=/app/group

RUN mkdir /.ssh
RUN chmod 766 /.ssh
RUN chmod 777 /app/

RUN mkdir /var/tmp/django_cache

COPY passwd.template /app/passwd.template
COPY group /app/group
RUN touch /app/passwd && chmod 777 /app/passwd 


RUN pip install virtualenv 
RUN ["/bin/bash", "-c", "/usr/bin/make virtualenv"]
RUN ["/bin/bash", "-c", "source platform_venv/bin/activate && pip install -r requirements.txt && export PYTHONPATH=$PWD:$PYTHONPATH"]
ENV DOCKER_FILES=./rendering_resource_manager_service/deployment/docker
COPY $DOCKER_FILES/local_settings.py /app/rendering_resource_manager_service/
COPY $DOCKER_FILES/gunicorn.sh /app/

RUN chmod 777 /app/gunicorn.sh

## Ports
EXPOSE 8383

#ENV TZ=Europe/Zurich
#RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

#USER bbpvizsoa
CMD /app/gunicorn.sh
