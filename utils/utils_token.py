from django.http import JsonResponse
from django.contrib.auth import authenticate, get_user_model
from UserManage.models import IMUser, TokenPoll
from django.contrib.auth.models import User
def token_check(user_token, token):
    if user_token != token:
        return JsonResponse({
            "code": -2,
            "info": "Token Error"
        })