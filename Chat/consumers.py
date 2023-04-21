from channels.exceptions import StopConsumer
from channels.generic.websocket import WebsocketConsumer
from pprint import *
import json

from UserManage.models import IMUser, TokenPoll
from FriendRelation.models import FriendList, Friend, AddList
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model, authenticate

# 定义一个列表，用于存放当前在线的用户
CONSUMER_OBJECT_LIST = []

CONSUMER2_OBJECT_LIST = []
USER_NAME_LIST = []


class ChatConsumer(WebsocketConsumer):

    def websocket_connect(self, message):
        """
        客户端浏览器发来连接请求之后就会被触发
        """

        # 服务端接收连接，向客户端浏览器发送一个加密字符串
        self.accept()
        # 连接成功
        CONSUMER_OBJECT_LIST.append(self)

    def websocket_receive(self, message):
        """
        客户端浏览器向服务端发送消息，此方法自动触发
        """

        print("接受到消息了", message)

        # 服务端给客户端回一条消息
        # self.send(text_data=message["text"])
        for obj in CONSUMER_OBJECT_LIST:
            obj.send(text_data=message["text"])

    def websocket_disconnect(self, message):
        """
        客户端浏览器主动断开连接
        """

        # 服务端断开连接
        CONSUMER_OBJECT_LIST.remove(self)
        raise StopConsumer()


# def send(self, text_data=None, bytes_data=None, close=False):
#     if text_data is not None:
#         super().send({"type": "websocket.send", "text": text_data})
#     elif bytes_data is not None:
#         super().send({"type": "websocket.send", "bytes": bytes_data})
#     else:
#         raise ValueError("You must pass one of bytes_data or text_data")
#     if close:
#         self.close(close)


def modify_add_request_list_with_username(other_username, add_list, answer, mode=0):
    """
    mode = 0 : add_list.reply
    mode = 1 : add_list.apply
    """
    index = search_ensure_false_request_index(other_username, add_list, mode=mode)
    if index == -1:
        return False
    if mode == 0:
        add_list.reply_answer[index] = answer  #
        add_list.reply_ensure[index] = True
    elif mode == 1:
        add_list.apply_answer[index] = answer  #
        add_list.apply_ensure[index] = True
    add_list.save()
    return True


def search_ensure_false_request_index(other_username, add_list, mode=0):
    if mode == 0:
        for li, peo in enumerate(add_list.reply_list):
            if peo == other_username and not add_list.reply_ensure[li]:
                return li
    elif mode == 1:
        for li, peo in enumerate(add_list.apply_list):
            if peo == other_username and not add_list.apply_ensure[li]:
                return li
    return -1


class FriendConsumer(WebsocketConsumer):
    # self看作当前触发事件的客户端

    def websocket_token_check(self, user_token, token):
        if user_token != token:
            self.close()

    def websocket_connect(self, message):
        """
        客户端浏览器发来连接请求之后触发，对应ws.onopen()
        """

        # message: 前端调用send发送的Json信息触发receive，dict格式
        # self：连接的客户端的数据结构，可以调用self.send()发送信息
        # self.send()：发送信息到客户端触发onmessage函数，可以发送json信息
        # self.scope: 本次连接的基本信息，dict格式

        # 服务端接收连接，向客户端浏览器发送一个加密字符串
        self.accept()
        # USER_NAME_LIST.append(username)
        CONSUMER2_OBJECT_LIST.append(self)

    def websocket_receive(self, message):
        """
        客户端浏览器向服务端发送消息，对应ws.send()
        """
        print(type(message))
        print(type(message['text']))
        print(message['text'])
        print(message)

        message = json.loads(message['text'])
        username = message['username']
        function = message['function']

        user_model = get_user_model()
        user = user_model.objects.get(username=username)
        im_user = IMUser.objects.get(user=user)

        if function == 'apply':
            # 修改数据库
            apply_from = message['from']
            apply_to = message['to']
            applyer_add_list = AddList.objects.get(user_name=apply_from)
            receiver_add_list = AddList.objects.get(user_name=apply_to)

            if not search_ensure_false_request_index(apply_to, applyer_add_list, mode=1) == -1:
                # 确保被回复前不能重复发送
                # mode=1意为在applyer_add_list.applylist中寻找apply_to
                self.send(text_data="Has Been Sent")
            else:
                applyer_add_list.apply_list.append(apply_to)
                applyer_add_list.apply_answer.append(False)
                applyer_add_list.apply_ensure.append(False)
                applyer_add_list.save()

                receiver_add_list.reply_list.append(apply_from)
                receiver_add_list.reply_answer.append(False)
                receiver_add_list.reply_ensure.append(False)
                receiver_add_list.save()

                # 若receiver在线申请发送到receiver
                return_field = {"applyer": apply_from}
                self.send(text_data=json.dumps(return_field))

                add_list = AddList.objects.get(user_name=username)
                return_field = []
                flen = len(add_list.apply_list)
                for li in range(flen):
                    return_field.append(
                        {
                            "username": add_list.apply_list[li],
                            "is_confirmed": add_list.apply_answer[li],
                            "make_sure": add_list.apply_ensure[li]
                        }
                    )
                self.send(text_data=json.dumps(
                    {
                        'function': 'applylist',
                        'applylist': return_field
                    }
                )
                )

        elif function == 'confirm':
            # 修改数据库
            apply_from = message['from']
            apply_to = message['to']
            receiver_add_list = AddList.objects.get(user_name=apply_to)
            applyer_add_list = AddList.objects.get(user_name=apply_from)

            modify_add_request_list_with_username(apply_from, receiver_add_list, True)
            modify_add_request_list_with_username(apply_to, applyer_add_list, True, mode=1)

            friend_list = FriendList.objects.get(user_name=username)
            friend_list.friend_list[0].append(apply_from)
            friend_list.save()

            friend = Friend(user_name=username,
                            friend_name=apply_from,
                            group_name=friend_list.group_list[0])
            friend.save()
            # 若applyer在线结果发送到applyer
            return_field = {"function": "confirm"}
            self.send(text_data=json.dumps(return_field))

        elif function == 'decline':
            # 修改数据库
            apply_from = message['from']
            apply_to = message['to']
            receiver_add_list = AddList.objects.get(user_name=apply_to)
            applyer_add_list = AddList.objects.get(user_name=apply_from)

            modify_add_request_list_with_username(apply_from, receiver_add_list, False)
            modify_add_request_list_with_username(apply_to, applyer_add_list, False, mode=1)

            return_field = {"function": "decline"}
            self.send(text_data=json.dumps(return_field))

        elif function == 'fetchapplylist':
            add_list = AddList.objects.get(user_name=username)
            return_field = []
            flen = len(add_list.apply_list)
            for li in range(flen):
                return_field.append(
                    {
                        "username": add_list.apply_list[li],
                        "is_confirmed": add_list.apply_answer[li],
                        "make_sure": add_list.apply_ensure[li]
                    }
                )
            self.send(text_data=json.dumps({
                'function': 'applylist',
                'applylist': return_field
            }
            )
            )
            # 发送list到client

        elif function == 'fetchreceivelist':
            add_list = AddList.objects.get(user_name=username)
            return_field = []
            flen = len(add_list.reply_list)
            for li in range(flen):
                return_field.append(
                    {
                        "username": add_list.reply_list[li],
                        "is_confirmed": add_list.reply_answer[li],
                        "make_sure": add_list.reply_ensure[li]
                    }
                )
            self.send(text_data=json.dumps(
                {
                    'function': 'receivelist',
                    'receivelist': return_field
                }
            )
            )
            # 发送list到client

        else:
            self.send(text_data=function + "Unknown Function")


def websocket_disconnect(self, message):
    """
    客户端浏览器主动断开连接，对应ws.onclose()
    """

    # USER_NAME_LIST.remove(username)
    CONSUMER2_OBJECT_LIST.remove(self)
    raise StopConsumer()
