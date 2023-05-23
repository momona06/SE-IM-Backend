"""
用户管理模块
"""
import json
import re
import random
import os
from aip import AipSpeech

from django.http import HttpRequest, HttpResponse, JsonResponse

from FriendRelation.models import FriendList, AddList, Friend
from utils.utils_cryptogram import encode, decode
from utils.utils_request import BAD_METHOD
from django.contrib.auth import authenticate, get_user_model

from django.contrib.auth.models import User
from UserManage.models import IMUser, TokenPoll, create_im_user, EmailCode, FileLoad
from django.core import mail

from Chat.models import ChatRoom, ChatTimeLine, Message, InviteList


def user_revise(req: HttpRequest):
    """
    用户修改个人信息
    """
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
                    for room in ChatRoom.objects.all()[::-1]:
                        for index, user in enumerate(room.mem_list):
                            if user == username:
                                room.mem_list[index] = revise_content
                                for index_, user_ in enumerate(room.manager_list):
                                    if user_ == username:
                                        room.manager_list[index_] = revise_content
                                        break
                                if room.master_name == username:
                                    room.master_name = revise_content
                                room.save()
                                break

                    friend_list = FriendList.objects.filter(user_name=username).first()
                    if friend_list is not None:
                        friend_list.user_name=revise_content
                        friend_list.save()

                    friend_user_list = Friend.objects.filter(user_name=username)
                    for i in friend_user_list:
                        if i is not None:
                            i.user_name = revise_content
                            i.save()

                    friend_other_list = Friend.objects.filter(friend_name=username)
                    for i in friend_other_list:
                        if i is not None:
                            i.user_name = revise_content
                            i.save()

                    user_add_list = AddList.objects.filter(user_name=username).first()

                    user_list = []

                    for reply_name in user_add_list.reply_list:
                        if reply_name not in user_list:
                            user_list.append(reply_name)

                            revise_username_in_other_add_list(reply_name, username, revise_content)

                    for apply_name in user_add_list.apply_list:
                        if apply_name not in user_list:
                            user_list.append(apply_name)

                            revise_username_in_other_add_list(apply_name, username, revise_content)

                    user_add_list.user_name = revise_content
                    user_add_list.save()

                    for message in Message.objects.all()[::-1]:
                        if message.sender == username:
                            message.sender = revise_content
                            message.save()
                        if message.type == 'invite' and decode(message.body) == username:
                            message.body = encode(revise_content)
                            message.save()

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


def user_logout(req: HttpRequest):
    """
    用户登出
    """
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


def user_cancel(req: HttpRequest):
    """
    用户注销
    """
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

            # message 中 用户名改为已停用 AccountSuspended

            suspended_account_name = 'AccountSuspended'

            user_add_list = AddList.objects.filter(user_name=username).first()

            user_list = []

            for reply_name in user_add_list.reply_list:
                if reply_name not in user_list:
                    user_list.append(reply_name)

                    delete_user_in_other_add_list(reply_name, username)

            for apply_name in user_add_list.apply_list:
                if apply_name not in user_list:
                    user_list.append(apply_name)

                    delete_user_in_other_add_list(apply_name, username)

            user_add_list.delete()

            for room in ChatRoom.objects.all()[::-1]:
                if username in room.mem_list:
                    index = room.mem_list.index(username)

                    room.mem_list.remove(username)

                    if username in room.manager_list:
                        room.manager_list.remove(username)

                    room.save()

                    timeline = ChatTimeLine.objects.filter(timeline_id=room.timeline_id).first()

                    # if room.is_private:
                    #     timeline.delete()
                    #     room.delete()
                    # elif username == room.master_name:
                    #     invite_list = InviteList.objects.filter(invite_list_id=room.invite_list_id).first()
                    #     invite_list.delete()
                    #
                    #     timeline.delete()
                    #     room.delete()
                    if not room.is_private:
                        for msg_id in timeline.msg_line:
                            message = Message.objects.get(msg_id=msg_id)

                            if message.sender == username:
                                message.sender = suspended_account_name
                                message.save()
                            if message.type == 'invite' and decode(message.body) == username:
                                message.body = encode(suspended_account_name)
                                message.save()

                            message.read_list.pop(index)

            return JsonResponse({
                "code": 0,
                "info": "User Canceled"
            })
        else:
            user_ = User.objects.filter(username=username).first()
            if user_ is None:
                return JsonResponse({
                    "code": -1,
                    "info": "User not Exists"
                })
            else:
                return JsonResponse({
                    "code": -1,
                    "info": "Wrong Password"
                })
    else:
        return BAD_METHOD


def delete_user_in_other_add_list(reply_name, username):
    """
    删除其他用户的add_list中的此用户
    """
    other_add_list = AddList.objects.filter(user_name=reply_name).first()
    lis = len(other_add_list.reply_list)
    for i, other_name in enumerate(other_add_list.reply_list[::-1]):
        if other_name == username:
            index = lis - i - 1
            del other_add_list.reply_list[index]
            del other_add_list.reply_ensure[index]
            del other_add_list.reply_answer[index]
    for i, other_name in enumerate(other_add_list.apply_list[::-1]):
        if other_name == username:
            index = lis - i - 1
            del other_add_list.apply_list[index]
            del other_add_list.apply_ensure[index]
            del other_add_list.apply_answer[index]

    other_add_list.save()

def revise_username_in_other_add_list(reply_name, username, revise_content):
    """
    更改其他用户的add_list中的用户名
    """
    other_add_list = AddList.objects.filter(user_name=reply_name).first()
    lis = len(other_add_list.reply_list)
    for i, other_name in enumerate(other_add_list.reply_list[::-1]):
        if other_name == username:
            index = lis - i - 1
            other_add_list.reply_list[index] = revise_content
            other_add_list.reply_ensure[index]= revise_content
            other_add_list.reply_answer[index]= revise_content
    for i, other_name in enumerate(other_add_list.apply_list[::-1]):
        if other_name == username:
            index = lis - i - 1
            other_add_list.apply_list[index]= revise_content
            other_add_list.apply_ensure[index]= revise_content
            other_add_list.apply_answer[index]= revise_content

    other_add_list.save()



def check_user_data_valid(username=None, password=None):
    """
    检查用户名和密码是否合法
    """
    pattern = r'^[a-zA-Z0-9]{6,20}$'
    if username is not None:
        if not re.match(pattern, username):
            return False
    if password is not None:
        if not re.match(pattern, password):
            return False
    return True


def check_email_valid(email):
    """
    检查邮箱是否合法
    """
    pattern = r'^[a-zA-Z0-9._]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,5}$'
    if re.match(pattern, email):
        return True
    else:
        return False


def user_register(request: HttpRequest):
    """
用户注册
    """
    if request.method == 'POST':
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
    """
    获取新的token
    """
    tem_token = random.randint(100_000_000_000, 999_999_999_999)
    while True:
        token_poll = TokenPoll.objects.filter(token=tem_token).first()
        if token_poll is None:
            TokenPoll.objects.create(token=tem_token)
            break
    return tem_token


def user_login(request, identity, password, login_filter):
    """
    用户登录
    """
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
                    # if not tem_im_user.is_login:
                    tem_im_user.token = get_new_token()
                    tem_im_user.is_login = True
                    tem_im_user.save()
                # else:
                #     return JsonResponse({
                #         "code": -7,
                #         "info": "User already login",
                #     })
                else:
                    return JsonResponse({
                        "code": -1,
                        "info": "Unexpected error"
                    })
                    # tem_im_user = create_im_user(tem_user,get_new_token())
                    # tem_im_user.save()
                avatar = os.path.join("/static/media/", str(tem_im_user.avatar))
                if avatar == "/static/media/":
                    avatar += "pic/default.jpeg"

                response = JsonResponse({
                    "username": tem_im_user.user.username,
                    "token": tem_im_user.token,
                    "avatar": avatar,
                    "code": 0,
                    "password": password,
                    "info": "Login Succeed",
                })
                response.headers["x-frame-options"] = "SAMEORIGIN"
                return response
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


def send_email(request: HttpRequest):
    """
    发送邮箱验证码
    """
    if request.method == 'POST':
        try:
            body = json.loads(request.body.decode("utf-8"))
            send_list = list()
            send_list.append(str(body['email']))
            sms_code = '%06d' % random.randint(0, 999999)
            cur_email = EmailCode(email=str(body['email']), code=sms_code)
            cur_email.save()
            mail.send_mail(
                subject='邮箱验证',
                message='您的验证码为：{0}'.format(sms_code),
                from_email='2840206224@qq.com',
                recipient_list=send_list
            )
            return JsonResponse({
                "code": 0,
                "info": "验证码已发送"
            })
        except Exception as e:
            print(e)
            return JsonResponse({
                "code": -1,
                "info": "发送失败"
            })


def bind_email(request):
    """
    绑定邮箱
    """
    if request.method == 'POST':
        try:
            body = json.loads(request.body.decode("utf-8"))
            cur_email = str(body["email"])
            cur_code = str(body['code'])
            cur_user = str(body["username"])
            user_model = get_user_model()
            user = user_model.objects.get(username=cur_user)
            if EmailCode.objects.filter(email=cur_email, code=cur_code).first() is not None:
                user.email = cur_email
                user.save()
                return JsonResponse({
                    "code": 0,
                    "info": "绑定成功"
                })
            else:
                return JsonResponse({
                    "code": -1,
                    "info": "验证码错误"
                })
        except Exception as e:
            print(e)
            return JsonResponse({
                "code": -1,
                "info": "验证码错误"
            })
        return None


def upload_avatar(request):
    """
    上传头像
    """
    if request.method == 'POST':
        try:
            cur_pic = request.FILES.get("avatar")
            # body = json.loads(request.body.decode("utf-8"))
            name = request.POST['username']
            cur_user = User.objects.filter(username=name).first()
            user = IMUser.objects.filter(user=cur_user).first()
            user.avatar = cur_pic
            user.save()
            return JsonResponse({
                "code": 0,
                "info": "successfully upload",
                "avatar": os.path.join("/static/media/", str(user.avatar))
            })
        except Exception as e:
            print(e)
            return JsonResponse({
                "code": -1,
                "info": "Unexpected error"
            })


def upload(request):
    """
    聊天文件上传
    """
    if request.method == 'POST':
        try:
            cur_file = request.FILES.get("file")
            file1 = FileLoad(file=cur_file)
            file1.save()
            response = JsonResponse({
                "code": 0,
                "info": "successfully upload",
                "file_url": os.path.join("/static/media/", str(file1.file))
            })
            response.headers["x-frame-options"] = "SAMEORIGIN"
            return response
        except Exception as e:
            print(e)
            return JsonResponse({
                "code": -1,
                "info": "Unexpected error"
            })

def audio_to_text(request):
    if request.method == 'POST':
        try:
            client = AipSpeech('33584366', 'XnMdNhg1mHCt64OZE4yPURVf', 'ZgFXLMRRvUQKnDEpvsHBu0T5ylV1aE7g')
            body = json.loads(request.body.decode("utf-8"))
            filename = str(body['url']).split('/')[-1]
            filepath = 'collect_static/media/file/'+filename
            with open(filepath, 'rb') as fp:
                result = client.asr(fp.read(), 'wav', 16000, {'dev_pid': 1537, })
            if result['err_no'] == 0:
                text = result['result'][0]
                return JsonResponse({
                    "code": 0,
                    "result": text
                })
            else:
                return JsonResponse({
                    "code": 0,
                    "result": 'error: not wav or too long'
                })
        except Exception as e:
            print(e)
            return JsonResponse({
                "code": -1,
                "info": "Unexpected error"
            })