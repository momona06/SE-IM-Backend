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

def check_sent_list(other_name, user_add_list):
    """
    只能通过reply_ensure判断是否处理过
    param: 另一个人的username, message, 查询者的add_list,
            mode=0 -> apply_list 实现有问题 默认mode=1
            mode=1 -> reply_list
    untreated: 真为有未处理的好友请求
    index: 未处理好友请求所在列表中的index
    """
    time = user_add_list.apply_list.count(other_name)
    index = -1
    untreated = False
    for i in range(0, time):
        # 0, last_index, index, next_index.....
        index = user_add_list.reply_list.index(other_name, index + 1)
        if not user_add_list.reply_ensure[index]:
            untreated = True

    return untreated, index


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
        direction = ''
        print(type(message))
        print(type(message['text']))
        print(message['text'])
        print(message)

        message = json.loads(message['text'])
        direction = message['direction']

        if direction == '/friend/client2server':
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
                '''
                确保之前发送的申请被回复前不能再发送申请
                '''
                # sent_boolean = self.check_sent_list(username, receiver_add_list)[0]
                #
                # if sent_boolean:
                #     self.send(text_data="Has Been Sent")
                # else:
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

            elif function == 'confirm':
                # 修改数据库
                apply_from = message['from']
                apply_to = message['to']
                receiver_add_list = AddList.objects.get(user_name=apply_to)
                applyer_add_list = AddList.objects.get(user_name=apply_from)
                sent_boolean, index_1 = check_sent_list(apply_from, receiver_add_list)
                if sent_boolean and not applyer_add_list.apply_list.count(username) == 0:
                    receiver_add_list.reply_answer[index_1] = True  #
                    receiver_add_list.reply_ensure[index_1] = True
                    receiver_add_list.save()

                    # TODO: index_2 大概率bug 思路是倒序获取这个apply_list中username的最新出现index
                    index_2 = len(applyer_add_list.apply_list) - list(reversed(applyer_add_list.apply_list)).index(username)
                    applyer_add_list.apply_ensure[index_2] = True  #
                    applyer_add_list.apply_ensure[index_2] = True
                    applyer_add_list.save()

                    friend_list = FriendList.objects.get(user_name=username)
                    friend_list.friend_list[0].append(apply_from)
                    friend_list.save()

                    friend = Friend(user_name=username,
                                    friend_name=friend_list.group_list[0],
                                    friend_list=friend_list)
                    friend.save()
                # 若applyer在线结果发送到applyer
                # return_field = {"function": "confirm"}
                # self.send(text_data=json.dumps(return_field))

            elif function == 'decline':
                # 修改数据库
                apply_from = message['from']
                apply_to = message['to']
                user_add_list = AddList.objects.get(user_name=apply_to)
                applyer_add_list = AddList.objects.get(user_name=apply_from)
                sent_boolean, index_1 = check_sent_list(apply_from, user_add_list)
                if sent_boolean and not applyer_add_list.apply_list.count(username) == 0:
                    user_add_list.reply_answer[index_1] = False
                    user_add_list.reply_ensure[index_1] = True
                    user_add_list.save()

                    # TODO: index_2 大概率bug 思路是倒序获取这个apply_list中username的最新出现index
                    index_2 = len(applyer_add_list.apply_list) - list(reversed(applyer_add_list.apply_list)).index(username)
                    applyer_add_list.apply_ensure[index_2] = False
                    applyer_add_list.reply_ensure[index_1] = True
                    applyer_add_list.save()

                    friend_list = FriendList.objects.get(user_name=username)
                    friend_list.friend_list[0].append(apply_from)
                    friend_list.save()

                    friend = Friend(user_name=username,
                                    friend_name=friend_list.group_list[0],
                                    friend_list=friend_list)
                    friend.save()
                # 若applyer在线结果发送到applyer
                # return_field = {"function": "decline"}
                # self.send(text_data=json.dumps(return_field))

            elif function == 'fetchapplylist':
                add_list = AddList.objects.get(user_name=username)
                return_field = {}
                flen = len(add_list.apply_list)
                for li in range(flen):
                    return_field.append(
                        {
                            "username": add_list.apply_list[li],
                            "is_confirmed": add_list.apply_answer[li],
                            "make_sure": add_list.apply_ensure[li]
                        }
                    )
                self.send(text_data=json.dumps(return_field))
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
                self.send(text_data=json.dumps(return_field))
                # 发送list到client

            else:
                self.send(text_data=function + "Unknown Function")

        else:
            self.send(text_data=direction + "Unknown Direction")



    def websocket_disconnect(self, message):
        """
        客户端浏览器主动断开连接，对应ws.onclose()
        """

        # USER_NAME_LIST.remove(username)
        CONSUMER2_OBJECT_LIST.remove(self)
        raise StopConsumer()
