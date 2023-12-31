from django.urls import path, include, re_path
# 新增
from django.views import static
from django.conf import settings

urlpatterns = [
    path('user/', include("UserManage.urls")),
    path('friend/', include("FriendRelation.urls")),
    re_path(r'^static/(?P<path>.*)$', static.serve, {'document_root': settings.STATIC_ROOT}, name='static'),
]
