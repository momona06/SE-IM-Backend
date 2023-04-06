import json
import re
import random

from django.http import HttpRequest, HttpResponse, JsonResponse
from utils.utils_request import BAD_METHOD
from django.contrib.auth import authenticate, get_user_model

from django.contrib.auth.models import User
from UserManage.models import IMUser, TokenPoll, CreateIMUser
from FriendRelation.models import FriendGroup


def createFriendGroup(req: HttpRequest):
    if req.method == "POST":
        body = json.loads(req.body.decode("utf-8"))
        username = str(body["username"])
        token = str(body["token"])
        fgroup_name = str(body["fgroup_name"])
        user_model = get_user_model()
        user = user_model.objects.filter(username=username).first()
        im_user = IMUser.objects.filter(user=user).first()
        if im_user.token != token:
            return JsonResponse({
                "code": -2,
                "info": "Token Error"
            })
        fgroup = FriendGroup.objects.filter(fgroup_name=fgroup_name).first()
        if fgroup:
            return JsonResponse({
                "code": -1,
                "info": "Group Already Exists"
            })
        new_fgroup = FriendGroup(fgroup_name=fgroup_name)
        new_fgroup.save()
        return JsonResponse({
            "code": 0,
            "info": "CreateGroup Succeed"
        })

    else:
        return BAD_METHOD

def getFriendList(req: HttpRequest):
    pass

def addFriendGroup(req: HttpRequest):
    pass

def searchUser(request):
    if request.method == "POST":
        try:
            body = json.loads(request.body.decode("utf-8"))
            my_username = str(body['my_username'])
            search_username = str(body['search_username'])
            users = User.objects.filter(username__icontains=search_username).exclude(username=my_username)
            usernames = [user.username for user in users]

            response_data = {
                "code": 0,
                "info": "Search Succeed",
                "search_user_list": usernames,
            }

            return JsonResponse(response_data, safe=False)
        except Exception as e:
            print(e)
            return JsonResponse({
                "code": -1,
                "info": "Unexpected error"
            })
    else:
        return BAD_METHOD


def checkFriendRelation(my_user,check_user):
    pass


def checkUser(request):
    if request.method == "POST":
        try:
            body = json.loads(request.body.decode("utf-8"))
            my_username = str(body['my_username'])
            check_name = str(body['check_name'])

            try:
                my_user = User.objects.get(username=my_username)
            except User.DoesNotExist:
                return JsonResponse({
                    "code": -3,
                    "info": "User not found"
                })

            try:
                check_user = User.objects.get(username=check_name)
            except User.DoesNotExist:
                return JsonResponse({
                    "code": -2,
                    "info": "User not found"
                })

            is_friend = checkFriendRelation(my_user,check_user)

            return JsonResponse({
                "code": 0,
                "username": check_user.username,
                "is_friend": is_friend,
                "info": "User found",
            })
        except Exception as e:
            print(e)
            return JsonResponse({
                "code": -1,
                "info": "Unexpected error"
            })
    else:
        return BAD_METHOD