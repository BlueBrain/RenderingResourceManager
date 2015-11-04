#Rendering resource manager
A service managing rendering resources in order to allow visualization web services. This service is in charge of:
- Keeping track of available Rendering Resources and their current state.
- Accepting asynchronous work requests (image generation or encoding), and schedule them according to an algorithm.
- Booking rendering resources for synchronous requests (typically for streaming videos)
- Deciding whether to create or remove rendering resources based on workload.
- Implementing some kind of stickiness based on the model loaded on a particular Renderer. This means that if two request for rendering based on the same model are received, they should both be sent to the same Renderer (the rationale behind this, is that it is very expensive to move the model around, because models contain big amounts of data).
- Rejecting connections when no resource is available

## ChangeLog

To keep track of the changes between releases check the
[changelog](doc/Changelog.md).

##Installation
Install python 2.6 or 2.7 , and virtualenv with apt-get and pip

### In the context of the Human Brain Project
Test execution from source
```
make virtualenv
. platform_venv/bin/activate
make test
```

### In any other context

```
virtualenv env
. ./env/bin/activate
pip install -r requirements.txt
```

### Initial Configuration

Create the database.
```
export PYTHONPATH=$PWD:$PYTHONPATH
cd rendering_resource_manager_service
python manage.py syncdb
```

Defining a user allows configuration via the admin web interface.

##Setup the Slurm username account and password
When starting rendering resources on a cluster, a specific account is required. The credentials for this account are defined in the service/settings.py file
```
##Slurm credentials (To be modified by deployment process)
SLURM_USERNAME = 'TO_BE_MODIFIED'
SLURM_PASSWORD = 'TO_BE_MODIFIED'
```

Start the server
```
python manage.py runserver localhost:9000 #runs the server
```

Configure the rendering resources by populating the database. Some examples are given in https://github.com/BlueBrain/RenderingResourceManager/blob/master/rendering_resource_manager_service/deployment/rrm/populateRRM.txt. Note that the DEBUG mode can also be used to populate the configuration via a web Browser (See the 'Getting familiar with the REST API' section of this document)

##Preparation for a commit submission
This will run pep8, pylint and unit tests
```
make verify_changes
```

##Getting familiar with the REST API
Edit service/settings.h and enable DEBUG mode
```
##SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
```

Start the server on port 9000 for example
```
python manage.py runserver localhost:9000
```

Browse the REST API documentation by opening the following URL in your browser
```
http://localhost:9000/rendering-resource-manager/v1/api-docs
```
