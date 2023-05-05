import json
import re
import random

from django.http import HttpRequest, HttpResponse, JsonResponse

from FriendRelation.models import FriendList, AddList, Friend
from utils.utils_request import BAD_METHOD
from django.contrib.auth import authenticate, get_user_model

from django.contrib.auth.models import User
from UserManage.models import IMUser, TokenPoll, create_im_user, EmailCode
from django.core import mail

from Chat.models import ChatRoom

def revise(req: HttpRequest):
    if req.method == "PUT":
        body = json.loads(req.body.decode("utf-8"))
        revise_field = str(body["revise_field"])
        revise_content = str(body["revise_content"])
        username = str(body["username"])
        token = str(body["token"])
        input_password = str(body["input_password"])
        user = authenticate(username=username, password=input_password)
        if user is None:
            return JsonResponse({
                "code": -1,
                "info": "User Not exists or Login State Error"
            })
        else:
            user_model = get_user_model()
            user_rev = user_model.objects.get(username=username)
            im_user = IMUser.objects.filter(user=user_rev).first()
            if token != im_user.token:
                return JsonResponse({
                    "code": -2,
                    "info": "Token Error"
                })
            else:
                if revise_field == "username":
                    chatroom_list = ChatRoom.objects.filter(master_name=username)

                    for i in chatroom_list:
                        i.master_name = revise_content

                    user_rev.username = revise_content


                elif revise_field == "password":
                    user_rev.set_password(revise_content)
                elif revise_field == "email":
                    user_rev.email = revise_content
                else:
                    return JsonResponse({
                        "code": -3,
                        "info": "Revise_field Error"
                    })
                user_rev.save()
                return JsonResponse({
                    "code": 0,
                    "info": "Revise Succeed"
                })

    else:
        return BAD_METHOD


def logout(req: HttpRequest):
    if req.method == "DELETE":
        body = json.loads(req.body.decode("utf-8"))
        username = str(body["username"])
        token = str(body["token"])
        user_model = get_user_model()
        user = user_model.objects.get(username=username)
        im_user = IMUser.objects.filter(user=user).first()


        if im_user.token == token:
            poll_token = TokenPoll.objects.filter(token=token).first()
            poll_token.delete()
            im_user.save()
            return JsonResponse({
                "code": 0,
                "info": "Logout Succeed"
            })

        else:
            return JsonResponse({
                "code": -1,
                "info": "Token Error"
            })

    else:
        return BAD_METHOD


def cancel(req: HttpRequest):
    if req.method == "DELETE":
        body = json.loads(req.body.decode("utf-8"))
        username = str(body["username"])
        input_password = str(body["input_password"])
        user = authenticate(username=username, password=input_password)
        if user is not None:
            user_del = IMUser.objects.get(user=user)
            user_del.delete()
            user_model = get_user_model()
            user = user_model.objects.get(username=username)
            user.delete()


            friend_list = FriendList.objects.filter(user_name=username).first()
            if friend_list is not None:
                friend_list.delete()

            friend_user_list = Friend.objects.filter(user_name=username)
            for i in friend_user_list:
                if i is not None:
                    i.delete()

            friend_other_list = Friend.objects.filter(friend_name=username)
            for i in friend_other_list:
                if i is not None:
                    i.delete()

            # 本账户的apply: 全部删除
            # 本账户的reply: 全部删除
            # (废弃)其他账户的apply, reply: ensure为真, answer为假, 用户名改为已停用 AccountSuspended

            # 以上三条废弃, 包含此用户名的信息全删

            '''
            a=[1,2,3,4,5]
            for i, k in enumerate(a[::-1]):
            l = len(a)
            print(str(l-i-1) + " " + str(k))
            
            4 5
            3 4
            2 3
            1 2
            0 1
            '''
            user_add_list = AddList.objects.filter(user_name=username)

            user_list = []

            for reply_name in user_add_list.reply_list:
                if not reply_name in user_list:
                    user_list.append(reply_name)

                    delete_user_in_other_add_list(reply_name, username)

            for apply_name in user_add_list.apply_list:
                if not apply_name in user_list:
                    user_list.append(apply_name)

                    delete_user_in_other_add_list(apply_name, username)

            user_add_list.delete()

            return JsonResponse({
                "code": 0,
                "info": "User Canceled"
            })
        else:

            return JsonResponse({
                "code": -1,
                "info": "User not Exists"
            })

    else:
        return BAD_METHOD


def delete_user_in_other_add_list(reply_name, username):
    other_add_list = AddList.objects.filter(user_name=reply_name).first()
    for i, other_name in other_add_list.reply_list[::-1]:
        if other_name == username:
            index = len(other_add_list.reply_list) - i - 1
            del other_add_list.reply_list[index]
            del other_add_list.reply_ensure[index]
            del other_add_list.reply_answer[index]
    for i, other_name in other_add_list.apply_list[::-1]:
        if other_name == username:
            index = len(other_add_list.apply_list) - i - 1
            del other_add_list.apply_list[index]
            del other_add_list.apply_ensure[index]
            del other_add_list.apply_answer[index]


'''
nzh code
'''


def check_user_data_valid(username=None, password=None):
    pattern = r'^[a-zA-Z0-9]{6,20}$'
    if username is not None:
        if not re.match(pattern, username):
            return False
    if password is not None:
        if not re.match(pattern, password):
            return False
    return True


def check_email_valid(email):
    pattern = r'^[a-zA-Z0-9._]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,5}$'
    if re.match(pattern, email):
        return True
    else:
        return False


def user_register(request: HttpRequest):
    if request.method == 'POST':
        # try:
            body = json.loads(request.body.decode("utf-8"))
            username = str(body["username"])
            password = str(body["password"])

            # check
            if check_user_data_valid(username, password):
                user = User.objects.filter(username=username).first()

                # unique
                if user is not None:
                    return JsonResponse({"code": -3, "info": "User already exists"})

                tem_user = User.objects.create_user(username=username, password=password)

                tem_im_user = create_im_user(tem_user, get_new_token())
                tem_im_user.save()

                group = ['我的好友']
                friend_list = FriendList(user_name=username, group_list=group, friend_list=list())
                friend_list.save()

                add_list = AddList(user_name=username,
                                   reply_list=list(), reply_answer=list(), reply_ensure=list(),
                                   apply_list=list(), apply_answer=list(), apply_ensure=list())
                add_list.save()

                return JsonResponse({
                    "code": 0,
                    "info": "Register Succeed",
                })
            else:
                return JsonResponse({
                    "code": -2,
                    "info": "Invalid Userdata",
                })
        # except Exception as e:
        #     print(e)
        #     return JsonResponse({
        #         "code": -1,
        #         "info": "Unexpected error"
        #     })
    else:
        return BAD_METHOD


def user_login_pre_treat(request: HttpRequest):
    """
    :param request:
    :return:
    """
    if request.method == "POST":
        body = json.loads(request.body.decode("utf-8"))
        username = str(body["username"])
        password = str(body["password"])
        email = str(body["email"])

        # login mode
        if not username == "":
            if not check_user_data_valid(username, password):
                return JsonResponse({
                    "code": -2,
                    "info": "Invalid Userdata"
                })
            return user_login(request, username, password, "username")
        elif not email == "":
            if not check_email_valid(email=email):
                return JsonResponse({
                    "code": -2,
                    "info": "Invalid Userdata"
                })
            return user_login(request, email, password, "email")
        else:
            return JsonResponse({
                "code": -1,
                "info": "Unexpected error"
            })

    else:
        return BAD_METHOD


def get_new_token():
    tem_token = random.randint(100_000_000_000, 999_999_999_999)
    while True:
        token_poll = TokenPoll.objects.filter(token=tem_token).first()
        if token_poll is None:
            TokenPoll.objects.create(token=tem_token)
            break
    return tem_token


def user_login(request, identity, password, login_filter):
    try:
        if login_filter == "username":
            user = User.objects.filter(username=identity).first()
        else:
            user = User.objects.filter(email=identity).first()

        if not user:
            return JsonResponse({
                "code": -4,
                "info": "User not exists",
            })
        else:
            if login_filter == "username":
                tem_user = authenticate(username=identity, password=password)
            else:
                cur_user = User.objects.get(email=identity).username
                tem_user = authenticate(username=cur_user, password=password)

            if tem_user:
                tem_im_user = IMUser.objects.filter(user=tem_user).first()
                if tem_im_user is not None:
                    tem_im_user.token = get_new_token()
                    tem_im_user.save()
                else:
                    return JsonResponse({
                        "code": -1,
                        "info": "Unexpected error"
                    })
                    # tem_im_user = create_im_user(tem_user,get_new_token())
                    # tem_im_user.save()

                return JsonResponse({
                    "username": tem_im_user.user.username,
                    "token": tem_im_user.token,
                    "code": 0,
                    "info": "Login Succeed",
                })
            else:
                return JsonResponse({
                    "code": -2,
                    "info": "Wrong Password",
                })
    except Exception as e:
        print(e)
        return JsonResponse({
            "code": -1,
            "info": "Unexpected error"
        })


def send_email(request:HttpRequest):
    if request.method == 'GET':
        return HttpResponse("send_email")
    if request.method == 'POST':
        try:
            body = json.loads(request.body.decode("utf-8"))
            send_list = []
            send_list.append(str(body['email']))
            sms_code = '%06d' % random.randint(0, 999999)
            cur_email = EmailCode(email=str(body['email']), code=sms_code)
            cur_email.save()
            mail.send_mail(
                subject = '邮箱验证',
                message = '您的验证码为：{0}'.format(sms_code),
                from_email = '2840206224@qq.com',
                recipient_list = send_list
            )
            return JsonResponse({
                "code" : 0,
                "info" : "验证码已发送"
            })
        except Exception as e:
            print(e)
            return JsonResponse({
                "code" : -1,
                "info" : "发送失败"
            })
def bind_email(request):
    if request.method == 'GET':
        return HttpResponse('bind_email')
    if request.method == 'POST':
        try:
            body = json.loads(request.body.decode("utf-8"))
            cur_email = str(body["email"])
            cur_code = str(body['code'])
            cur_user = str(body["username"])
            if EmailCode.objects.filter(email=cur_email, code=cur_code).first() is not None:
                user_model = get_user_model()
                user = user_model.objects.get(username=cur_user)
                user.email = cur_email
                user.save()
                return JsonResponse({
                    "code": 0,
                    "info":"绑定成功"
                })
        except Exception as e:
            print(e)
            return JsonResponse({
                "code": -1,
                "info": "验证码错误"
            })
        return None
