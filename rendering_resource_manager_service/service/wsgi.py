"""
WSGI config for rendering_resource_manager_service project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/howto/deployment/wsgi/
"""

from django.core.wsgi import get_wsgi_application
from rendering_resource_manager_service.session.management import keep_alive_thread
from rendering_resource_manager_service.session.models import Session

application = get_wsgi_application()

# Start keep-alive thread
# pylint: disable=E1101
thread = keep_alive_thread.KeepAliveThread(Session.objects)
thread.setDaemon(True)  # This guaranties that the thread is destroyed when the main process ends
thread.start()
