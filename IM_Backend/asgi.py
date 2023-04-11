"""
ASGI config for IM_Backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/asgi/
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'IM_Backend.settings')
django.setup()


from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

from Chat.consumers import ChatConsumer, FriendConsumer
from django.urls import path



websocket_urlpatterns = [
    path('chat', ChatConsumer.as_asgi()),
    path('friend/addfriend', FriendConsumer.as_asgi()),
    path('friend/receivefriend', FriendConsumer.as_asgi()),
    path('friend/getfriendaddlist', FriendConsumer.as_asgi())
]

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": AuthMiddlewareStack(
            URLRouter(
                websocket_urlpatterns
            )
        )
    }
)
