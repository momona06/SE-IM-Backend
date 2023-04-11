import json
import re
import random

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.contrib.auth import authenticate, get_user_model

from utils.utils_request import template_request, BAD_METHOD
from utils.utils_token import token_check_http

from django.contrib.auth.models import User
from UserManage.models import IMUser, TokenPoll, CreateIMUser
from FriendRelation.models import FriendList, Friend

def create_friend_group(req: HttpRequest):
    if req.method == "POST":
        body = json.loads(req.body.decode("utf-8"))
        username = str(body["username"])
        token = str(body["token"])
        fgroup_name = str(body["fgroup_name"])
        user_model = get_user_model()
        user = user_model.objects.filter(username=username).first()
        im_user = IMUser.objects.filter(user=user).first()

        token_check_http(im_user.token, token)

        flist = FriendList.objects.get(user_name=username)
        for gname in flist.group_list:
            if gname == fgroup_name:
                return JsonResponse({
                    "code": -1,
                    "info": "Group Already Exists",
                })

        flist.group_list.append(fgroup_name)
        flist.save()
        return JsonResponse({
            "code": 0,
            "info": "CreateGroup Succeed"
        })

    else:
        return BAD_METHOD

def get_friend_list(req: HttpRequest):
    if req.method == "POST":
        body = json.loads(req.body.decode("utf-8"))
        username = str(body["username"])
        token = str(body["token"])

        user_model = get_user_model()
        user = user_model.objects.filter(username=username).first()
        im_user = IMUser.objects.filter(user=user).first()

        token_check_http(im_user.token, token)

        flist = FriendList.objects.get(user_name=username)

        return_list = {}

        flist_len = len(flist.group_list)

        for i in range(flist_len):
            midlist = []
            for friend_name in flist.friend_list[i]:
                midlist.append(friend_name)
            return_list[flist.group_list[i]] = midlist
        return JsonResponse({
            "code": 0,
            "info": "Friendlist get",
            "friendlist": return_list
        })

    else:
        return BAD_METHOD


def add_friend_group(req: HttpRequest):
    if req.method == "PUT":
        body = json.loads(req.body.decode("utf-8"))
        username = str(body["username"])
        token = str(body["token"])
        fgroup_name = str(body["fgroup_name"])
        friend_name = str(body["friend_name"])

        user_model = get_user_model()
        user = user_model.objects.filter(username=username).first()
        im_user = IMUser.objects.filter(user=user).first()

        token_check_http(im_user.token, token)

        friend = Friend.objects.filter(user_name=username, friend_name=friend_name).first()
        flist = FriendList.objects.filter(user_name=username).first()

        lis = 0
        for li, group in enumerate(flist.group_list):
            if group == fgroup_name:
                lis = li

        flist.friend_list[lis].append(friend_name)
        flist.save()

    else:
        return BAD_METHOD

