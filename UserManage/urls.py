from django.urls import path
import UserManage.views as views

urlpatterns = [
    path('login', views.user_login_pre_treat),
    path('register', views.user_register),
    path('email', views.bind_email),
    path('send_email', views.send_email),
    path('cancel', views.user_cancel),
    path('logout', views.user_logout),
    path('revise', views.user_revise),
    path('upload', views.upload_avatar),
    path('uploadfile', views.upload),
    path('audio', views.audio_to_text)
]