from django.http import JsonResponse
from django.contrib.auth import authenticate, get_user_model
from UserManage.models import IMUser, TokenPoll
from django.contrib.auth.models import User
def token_check_http(user_token, token):
    return user_token != token


