from django.urls import path
import FriendRelation.views as views

urlpatterns = [
    path('createfgroup', views.createFriendGroup),
    path('getfriendlist', views.getFriendList),
    path('addfgroup', views.addFriendGroup),
]

