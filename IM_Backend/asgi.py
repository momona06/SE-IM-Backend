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
    path('wsconnect', FriendConsumer.as_asgi())
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
