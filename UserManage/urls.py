from django.urls import path
import UserManage.views as views

urlpatterns = [
    path('login', views.user_login_pre_treat),
    path('register', views.user_register),
    path('email', views.bind_email),
    path('send_email', views.send_email),
    path('cancel', views.cancel),
    path('logout', views.logout),
    path('revise', views.revise),
    path('upload', views.upload_avatar),
    path('uploadpic', views.upload_avatar)
]