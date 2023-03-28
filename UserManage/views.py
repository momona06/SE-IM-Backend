from django.shortcuts import render

import json
from django.http import HttpRequest, HttpResponse
from UserManage.models import User
from django.http import JsonResponse
from utils.utils_request import BAD_METHOD, request_failed, return_field, request_success_M, \
    request_failed_M
from utils.utils_require import MAX_CHAR_LENGTH, CheckRequire, require
from utils.utils_time import get_timestamp


def register(req: HttpRequest):
    """
    :param req:
    :return:
    """
    # body的json内容处理
    if req.method == "POST":

        body = json.loads(req.body.decode("utf-8"))
        username = str(body["username"])
        password = str(body["password"])
        user = User.objects.filter(username=username).first()  # If not exists, return None

        if not user:
            user = User(username=username, password=password)
            user.save()
            return request_success_M({"isCreate": True})
        else:
            return request_failed_M({"isCreate": False})



    elif req.method == "GET":
        return JsonResponse({
            "Test": "Well Get"
        })
    else:
        return BAD_METHOD


def login(req: HttpRequest):
    """
    :param req:
    :return:
    """
    if req.method == "POST":
        body = json.loads(req.body.decode("utf-8"))
        username = str(body["username"])
        password = str(body["password"])
        user = User.objects.filter(username=username).first()
        if not user:
            return JsonResponse({
                "code": -1,
                "info": "User not exists",
            })
        else:
            if user.password == password:
                return JsonResponse({
                    "code": 0,
                    "info": "Login Succeed",
                })
            else:
                return JsonResponse({
                    "code": -2,
                    "info": "Wrong Password",
                })

    else:
        return BAD_METHOD
