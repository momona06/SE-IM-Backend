from django.urls import path
from Chat.consumers import ChatConsumer

websocket_urlpatterns = [
    path('chat', ChatConsumer.as_asgi())
]