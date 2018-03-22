# In case of insufficient resources on OpenShift,
# check https://bbpteam.epfl.ch/project/spaces/display/INFRA/OpenShift#OpenShift-OpenShiftbuildsexitswitherrorcode137.

FROM nginx:alpine
WORKDIR /app
ADD . /app

RUN apk update && apk add openssh make py-pip \
bash python2-dev gcc libc-dev \
postgresql-dev supervisor && \
pip install virtualenv

RUN /usr/bin/make virtualenv && source platform_venv/bin/activate && \
pip install -r requirements.txt

ENV SLURM_SSH_KEY=/app/slurm-ssh-key

RUN mkdir /etc/nginx/sites-available && mkdir /etc/nginx/sites-enabled
RUN cd rendering_resource_manager_service && pwd

ENV DOCKER_FILES=./rendering_resource_manager_service/deployment/docker
COPY $DOCKER_FILES/supervisord.conf /etc/supervisord.conf 
COPY $DOCKER_FILES/rrm.conf /etc/nginx/sites-available/
COPY $DOCKER_FILES/nginx.conf /etc/nginx/nginx.conf
COPY $DOCKER_FILES/programs.ini /etc/supervisor.d/
COPY $DOCKER_FILES/local_settings.py /app/rendering_resource_manager_service/
RUN ln -s /etc/nginx/sites-available/rrm.conf /etc/nginx/sites-enabled/rrm.conf

## Ports
EXPOSE 80

## Run supervisor
CMD /usr/bin/supervisord -c  /etc/supervisord.conf
