from django.urls import path, include
import UserManage.views as views

urlpatterns = [
    path('user/login', views.login),
    path('user/register', views.register),
]