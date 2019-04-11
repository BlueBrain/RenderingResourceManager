#!/bin/bash

export USER_ID=$(id -u)
export GROUP_ID=$(id -g)
envsubst < /app/passwd.template > /app/passwd
source /app/platform_venv/bin/activate && gunicorn rendering_resource_manager_service.service.wsgi -w 4 -b 0.0.0.0:8383 --log-file -
