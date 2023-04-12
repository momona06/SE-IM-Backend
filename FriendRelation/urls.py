from django.urls import path
import FriendRelation.views as views

urlpatterns = [
    path('createfgroup', views.create_friend_group),
    path('getfriendlist', views.get_friend_list),
    path('addfgroup', views.add_friend_group),
    path('searchuser', views.searchUser),
    path('checkuser', views.checkUser),
    path('deletefriend', views.delete_friend)
]

