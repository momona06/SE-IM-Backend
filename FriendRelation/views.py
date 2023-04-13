import json
import re
import random

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.contrib.auth import authenticate, get_user_model

from utils.utils_request import template_request, BAD_METHOD
from utils.utils_token import token_check_http

from django.contrib.auth.models import User
from UserManage.models import IMUser, TokenPoll, CreateIMUser
from FriendRelation.models import FriendList, Friend, AddList


def delete_friend(req: HttpRequest):
    if req.method == "DELETE":
        try:
            body = json.loads(req.body.decode("utf-8"))
            username = str(body["username"])
            token = str(body["token"])
            friend_name = str(body["friend_name"])
            user_model = get_user_model()
            user = user_model.objects.filter(username=username).first()
            im_user = IMUser.objects.filter(user=user).first()
            if im_user.token != token:
                return JsonResponse({
                    'code': -2,
                    'info': "Token Error",
                })

            friend = Friend.objects.filter(friend_name=friend_name, user_name=username).first()

            if friend is None:
                return JsonResponse({
                    'code': -1,
                    'info': 'Friend Not Exists'
                })

            flist = FriendList.objects.get(user_name=username)
            for friend_name in flist.friend_list:
                if friend.friend_name == friend_name:
                    friend_name.remove()
                    break
            flist.save()
            friend.delete()
            return JsonResponse({
                'code': 0,
                'info': "Delete Friend Succeed"
            })
        except Exception as e:
            print(e)
            return JsonResponse({
                "code": -5,
                "info": "Unexpected Error"
            })


    else:
        return BAD_METHOD


def delete_friend_group(req: HttpRequest):
    if req.method == "DELETE":
        try:
            body = json.loads(req.body.decode("utf-8"))
            username = str(body["username"])
            token = str(body["token"])
            fgroup_name = str(body["fgroup_name"])
            user_model = get_user_model()
            user = user_model.objects.filter(username=username).first()
            im_user = IMUser.objects.filter(user=user).first()
            if im_user.token != token:
                return JsonResponse({
                    'code': -2,
                    'info': "Token Error",
                })

            flist = FriendList.objects.filter(user_name=username).first()
            group_exist = False
            lis = 0
            for li, gname in enumerate(flist.group_list):
                if gname == fgroup_name:
                    group_exist = True
                    lis = li
                    break

            if not group_exist:
                return JsonResponse({
                    'code': -4,
                    'info': 'Friend Not Exists'
                })
            empty = True
            for friend_name in flist.friend_list:
                friend = Friend.objects.filter(friend_name=friend_name,user_name=username).first()
                if friend is None :
                    break
                if friend.group_name == fgroup_name:
                    empty = False
                    break

            if not empty:
                return JsonResponse({
                    'code': -5,
                    'info': "Number of Friend Not 0"
                })

            del flist.group_list[lis]
            flist.save()
            return JsonResponse({
                'code': 0,
                'info': "Delete Friend Group Succeed"
            })
        except Exception as e:
            print(e)
            return JsonResponse({
                "code": -5,
                "info": "Unexpected Error"
            })

    else:
        return BAD_METHOD


def create_friend_group(req: HttpRequest):
    if req.method == "POST":
        try:
            body = json.loads(req.body.decode("utf-8"))
            username = str(body["username"])
            token = str(body["token"])
            fgroup_name = str(body["fgroup_name"])
            user_model = get_user_model()
            user = user_model.objects.filter(username=username).first()
            im_user = IMUser.objects.filter(user=user).first()

            if im_user.token != token:
                return JsonResponse({
                    'code': -2,
                    'info': "Token Error",
                })

            flist = FriendList.objects.get(user_name=username)
            for gname in flist.group_list:
                if gname == fgroup_name:
                    return JsonResponse({
                        "code": -1,
                        "info": "Group Already Exists",
                    })

            flist.group_list.append(fgroup_name)
            # flist.friend_list.append([])
            flist.save()
            return JsonResponse({
                "code": 0,
                "info": "CreateGroup Succeed"
            })
        except Exception as e:
            print(e)
            return JsonResponse({
                "code": -5,
                "info": "Unexpected Error"
            })

    else:
        return BAD_METHOD


def get_friend_list(req: HttpRequest):
    if req.method == "POST":
        try:
            body = json.loads(req.body.decode("utf-8"))
            username = str(body["username"])
            token = str(body["token"])

            user_model = get_user_model()
            user = user_model.objects.filter(username=username).first()
            im_user = IMUser.objects.filter(user=user).first()

            if im_user.token != token:
                return JsonResponse({
                    'code': -2,
                    'info': "Token Error",
                    'friendlist': []
                })

            flist = FriendList.objects.get(user_name=username)

            return_list = []

            flist_len = len(flist.group_list)

            for i in range(flist_len):
                for friend_name in flist.friend_list[i]:
                    friend = Friend.objects.filter(friend_name=friend_name, user_name=username).first()
                    group_name = friend.group_name
                    return_list.append({"username": friend_name, "groupname": group_name})
            return JsonResponse({
                "code": 0,
                "info": "Friendlist Get",
                "friendlist": return_list
            })
        except Exception as e:
            print(e)
            return JsonResponse({
                "code": -5,
                "info": "Unexpected Error"
            })

    else:
        return BAD_METHOD


def add_friend_group(req: HttpRequest):
    if req.method == "PUT":
        try:
            body = json.loads(req.body.decode("utf-8"))
            username = str(body["username"])
            token = str(body["token"])
            fgroup_name = str(body["fgroup_name"])
            friend_name = str(body["friend_name"])

            user_model = get_user_model()
            user = user_model.objects.filter(username=username).first()
            im_user = IMUser.objects.filter(user=user).first()

            if im_user.token != token:
                return JsonResponse({
                    'code': -2,
                    'info': "Token Error",
                })

            friend = Friend.objects.filter(user_name=username, friend_name=friend_name).first()
            flist = FriendList.objects.filter(user_name=username).first()

            lis = 0
            for li, group in enumerate(flist.group_list):
                if group == fgroup_name:
                    lis = li
    
            # flist.friend_list[lis].append(friend_name)
            for friend_name in flist.friend_list:
                friend = Friend.objects.filter(friend_name=friend_name,user_name=username).first()
                if friend.friend_name == friend_name:
                    friend.group_name = fgroup_name
                    break
            flist.save()
            return JsonResponse({
                "code": 0,
                "info": "AddGroup Succeed"
            })
        except Exception as e:
            print(e)
            return JsonResponse({
                "code": -5,
                "info": "Unexpected Error"
            })

    else:
        return BAD_METHOD


def search_user(request):
    if request.method == "POST":
        try:
            body = json.loads(request.body.decode("utf-8"))
            my_username = str(body['my_username'])
            search_username = str(body['search_username'])
            users = User.objects.filter(username__icontains=search_username).exclude(username=my_username)
            usernames = list()
            for user in users:
                usernames.append(user.username)

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


def check_friend_relation(my_username, check_name):
    flist = FriendList.objects.get(user_name=my_username)
    for i in flist.friend_list:
        if check_name in i:
            return True
    return False


def check_user(request):
    if request.method == "POST":
        try:
            body = json.loads(request.body.decode("utf-8"))
            my_username = str(body['my_username'])
            check_name = str(body['check_name'])
            token = str(body['token'])

            if my_username == check_name:
                return JsonResponse({
                    "code": -4,
                    "info": "The Query User Is The Same As User"
                })

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
                    "code": -20,
                    "info": "User not found"
                })

            im_user = IMUser.objects.filter(user=my_user).first()

            if im_user.token != token:
                return JsonResponse({
                    'code': -2,
                    'info': "Token Error",
                })

            is_friend = check_friend_relation(my_username, check_name)

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