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


