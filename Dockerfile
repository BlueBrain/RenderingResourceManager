# In case of insufficient resources on OpenShift,
# check https://bbpteam.epfl.ch/project/spaces/display/INFRA/OpenShift#OpenShift-OpenShiftbuildsexitswitherrorcode137.

FROM alpine
WORKDIR /app
ADD . /app

RUN apk update && apk add openssh make py-pip git \
bash python2-dev gcc libc-dev \
postgresql-dev supervisor && \
pip install virtualenv

RUN ["/bin/bash", "-c", "source platform_venv/bin/activate && pip install -r requirements.txt && export PYTHONPATH=$PWD:$PYTHONPATH"]
RUN ["/bin/bash", "-c", "chmod 700 ssh-privatekey"]
RUN ["/bin/bash", "-c", "/usr/bin/make virtualenv"]

ENV SLURM_SSH_KEY=/app/slurm-ssh-key

ENV SLURM_HOSTS=['bbpviz1.cscs.ch']
ENV SLURM_PROJECT=TEST
ENV SLURM_USERNAME=bbpvizsoa
ENV SLURM_SSH_KEY=/app/slurm-ssh-key
ENV SLURM_DEFAULT_TIME=2
ENV SLURM_DEFAULT_QUEUE=2

ENV DB_NAME=vizdemos_dev
ENV DB_HOST=bbpdbsrv06.bbp.epfl.ch
ENV DB_PORT=5432
ENV DB_USER=vizdemos_dev
ENV RRM_VERSION=1
ENV RRM_SERVICE_PORT=8383

RUN mkdir /var/tmp/django_cache

RUN cd rendering_resource_manager_service && pwd

ENV DOCKER_FILES=./rendering_resource_manager_service/deployment/docker
COPY $DOCKER_FILES/local_settings.py /app/rendering_resource_manager_service/
COPY $DOCKER_FILES/gunicorn.sh /app/
RUN chmod +x /app/gunicorn.sh

## Ports
EXPOSE 8383

CMD /app/gunicorn.sh
