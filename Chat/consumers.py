from channels.exceptions import StopConsumer
from channels.generic.websocket import WebsocketConsumer
from pprint import *
import json

from UserManage.models import IMUser, TokenPoll
from FriendRelation.models import FriendList, Friend, AddList
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model

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

class FriendConsumer(WebsocketConsumer):
    # self看作当前触发事件的客户端

    def websocket_token_check(self, user_token, token):
        if user_token != token:
            self.close()

    def websocket_connect(self, message):
        """
        客户端浏览器发来连接请求之后触发，对应ws.onopen
        """

        # message: 前端的Json信息，dict格式
        # self：连接的客户端的数据结构，可以调用self.send()发送信息
        # self.send()：发送信息到客户端，可以发送json信息
        # self.scope: 本次连接的基本信息，dict格式

        # print("连接成功", message)
        # print("scope =")
        # pprint(self.scope)
        # print("scope.path =")
        # pprint(self.scope['path'])

        # username = message["username"]
        # password = message["password"]
        print(message)
        # 服务端接收连接，向客户端浏览器发送一个加密字符串
        self.accept()
        CONSUMER2_OBJECT_LIST.append(self)

    def websocket_receive(self, message):
        """
        客户端浏览器向服务端发送消息，对应ws.send()
        """

        # print("接受到消息了", message)
        # pprint(self.scope)

        ws_url = self.scope['path']
        if ws_url == '/friend/addfriend':
            username = message['username']
            token = message['token']
            friend_name = message['friend_name']

            user_model = get_user_model()
            user = user_model.objects.filter(username=username).first()
            im_user = IMUser.objects.filter(user=user).first()

            self.websocket_token_check(im_user.token, token)

            user_add_list = AddList.objects.get(user_name=username)
            friend_add_list = AddList.objects.get(user_name=friend_name)

            # 确保之前发送的申请被回复前不能再发送申请
            sent_boolean = self.checkSentList(username, friend_add_list)[0]

            if sent_boolean:
                self.send(text_data=message["Has Been Sent"])
            else:
                user_add_list.apply_list.append(friend_name)
                user_add_list.apply_answer.append(False)
                user_add_list.save()

                friend_add_list.reply_list.append(username)
                friend_add_list.reply_answer.append(False)
                friend_add_list.reply_ensure.append(False)
                friend_add_list.save()


        elif ws_url == '/friend/receivefriend':
            username = message['username']
            token = message['token']
            requester_name = message['requester_name']
            agreement = message['agreement']

            user_model = get_user_model()
            user = user_model.objects.filter(username=username).first()
            im_user = IMUser.objects.filter(user=user).first()

            self.websocket_token_check(im_user.token, token)

            user_add_list = AddList.objects.get(user_name=username)
            requester_add_list = AddList.objects.get(user_name=requester_name)

            """
            我们需要对user_add_list做一次修改，然后再对requester_add_list做一次修改
            """
            # if agreement:
            # else:

            sent_boolean, index_1 = self.checkSentList(requester_name, user_add_list)
            if sent_boolean and not requester_add_list.apply_list.count(username) == 0:
                user_add_list.reply_answer[index_1] = agreement
                user_add_list.reply_ensure[index_1] = True
                user_add_list.save()

                # TODO: index_2 大概率bug 思路是倒序获取这个apply_list中username的最新出现index
                index_2 = len(requester_add_list.apply_list) - \
                          list(reversed(requester_add_list.apply_list)).index(username)
                requester_add_list.apply_ensure[index_2] = agreement
                requester_add_list.save()


        elif ws_url == '/friend/getfriendaddlist':
            username = message['username']
            token = message['token']

            user_model = get_user_model()
            user = user_model.objects.filter(username=username).first()
            im_user = IMUser.objects.filter(user=user).first()

            self.websocket_token_check(im_user.token, token)


        else:
            self.close()

        # 服务端给客户端回一条消息
        # for obj in CONSUMER2_OBJECT_LIST:
        #    obj.send(text_data=message["text"])
        '''
        obj.send 对应ws.onmessage()
        '''

        # self.send(
        #   text_data=message["text"]
        # )
        # self.send(text_data=json.dumps({
        #   'message': message
        # }))

    def checkSentList(self, other_name, user_add_list):
        """
        只能通过reply_ensure判断是否处理过
        param:  另一个人的username, message, 查询者的add_list,
                # mode=0->apply_list 实现有问题 默认mode=1
                mode=1->reply_list
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

    def websocket_disconnect(self, message):
        """
        客户端浏览器主动断开连接，对应ws.onclose()
        """
        print("断开连接", message)

        username = message['username']
        token = message['token']

        user_model = get_user_model()
        user = user_model.objects.filter(username=username).first()
        im_user = IMUser.objects.filter(user=user).first()

        self.websocket_token_check(im_user.token, token)

        # 服务端断开连接
        USER_NAME_LIST.remove(user_name)
        CONSUMER2_OBJECT_LIST.remove(self)
        raise StopConsumer()
