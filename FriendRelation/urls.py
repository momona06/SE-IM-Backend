from django.urls import path
import FriendRelation.views as views

urlpatterns = [
    path('createfgroup', views.create_friend_group),
    path('addfgroup', views.add_friend_group),
    path('searchuser', views.search_user),
    path('checkuser', views.check_user),
    path('deletefriend', views.delete_friend),
    path('deletefgroup', views.delete_friend_group)
]
