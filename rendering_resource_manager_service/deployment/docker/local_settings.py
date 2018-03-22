import os
import socket

ALLOWED_HOSTS = (
   'localhost',
   '127.0.0.1',
    socket.getfqdn(),
    'rrm.apps.bbp.epfl.ch'
)

CORS_ORIGIN_WHITELIST = (
   '127.0.0.1:'+os.environ['RRM_SERVICE_PORT'],
   'localhost:'+os.environ['RRM_SERVICE_PORT'],
    socket.getfqdn()+':'+ os.environ['RRM_SERVICE_PORT'],
   'rrm.apps.bbp.epfl.ch:'+ os.environ['RRM_SERVICE_PORT']
)

APPLICATION_NAME = 'rendering-resource-manager'
APPLICATION_VERSION = os.environ['RRM_VERSION'] 
API_VERSION = 'v1'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'USER': os.environ['DB_USER'],
        'PASSWORD': os.environ['DB_PASSWORD'],
        'HOST' : os.environ['DB_HOST'],
        'PORT' : os.environ['DB_PORT'],
        'NAME': os.environ['DB_NAME']
    }
}
RESOURCE_ALLOCATOR = 'SLURM'

SLURM_USERNAME = os.environ['SLURM_USERNAME']
SLURM_SSH_KEY =  os.environ['SLURM_SSH_KEY']
SLURM_PROJECT = os.environ['SLURM_PROJECT']
SLURM_HOSTS = os.environ['SLURM_HOSTS']
SLURM_DEFAULT_QUEUE = os.environ['SLURM_DEFAULT_QUEUE']
SLURM_DEFAULT_TIME = os.environ['SLURM_DEFAULT_TIME']
