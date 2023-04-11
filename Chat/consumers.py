from channels.exceptions import StopConsumer
from channels.generic.websocket import WebsocketConsumer
from pprint import *
import json
# 定义一个列表，用于存放当前在线的用户
CONSUMER_OBJECT_LIST = []

CONSUMER2_OBJECT_LIST = []


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
    def websocket_connect(self, message):
        """
        客户端浏览器发来连接请求之后触发，对应ws.onopen
        """

        # message: 前端的Json信息，dict格式
        # self：连接的客户端的数据结构，可以调用self.send()发送信息
        # self.send()：发送信息到客户端，可以发送json信息
        # self.scope: 本次连接的基本信息，dict格式

        print("连接成功", message)
        pprint(self.scope)
        # 服务端接收连接，向客户端浏览器发送一个加密字符串
        self.accept()
        CONSUMER2_OBJECT_LIST.append(self)
        self.send(text_data="accept connection")

    def websocket_receive(self, message):
        """
        客户端浏览器向服务端发送消息，对应ws.send()
        """

        print("接受到消息了", message)
        pprint(self.scope)

        # 服务端给客户端回一条消息
        for obj in CONSUMER2_OBJECT_LIST:
           obj.send(text_data=message["text"])
        '''
        obj.send 对应ws.onmessage()
        '''


        # self.send(
        #   text_data=message["text"]
        # )
        # self.send(text_data=json.dumps({
        #   'message': message
        # }))



    def websocket_disconnect(self, message):
        """
        客户端浏览器主动断开连接，对应ws.onclose()
        """
        print("断开连接", message)
        # 服务端断开连接
        CONSUMER2_OBJECT_LIST.remove(self)
        raise StopConsumer()