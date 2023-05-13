# from asgiref.sync import sync_to_async
# from django.contrib.auth.models import User
#
# from Chat.consumers import UserConsumer
# from django.test import TestCase
#
# from channels.testing import WebsocketCommunicator
#
# from FriendRelation.models import FriendList, AddList
#
# USERNAME_0 = "test00"
# PASSWORD_0 = "123456"
# USERNAME_1 = "test01"
# PASSWORD_1 = "123456"
#
#
# async def register(username, password):
#     tem = await sync_to_async(User.objects.create_user)(username=username, password=password)
#     await sync_to_async(tem.save)()
#
#     group = ['我的好友']
#     friend_list = await sync_to_async(FriendList)(user_name=username, group_list=group, friend_list=list())
#     await sync_to_async(friend_list.save)()
#
#     add_list = await sync_to_async(AddList)(user_name=username,
#                            reply_list=list(), reply_answer=list(), reply_ensure=list(),
#                            apply_list=list(), apply_answer=list(), apply_ensure=list())
#     await sync_to_async(add_list.save)()
#
#
# class MyConsumerTestCase(TestCase):
#     def __init__(self, methodName: str = ...):
#         super().__init__(methodName)
#         await register(USERNAME_0, PASSWORD_0)
#
#     async def test_heartbeat(self):
#
#
#         communicator_0 = WebsocketCommunicator(UserConsumer.as_asgi(), "/ws/")
#
#         # 连接 WebSocket
#         connected, _ = await communicator_0.connect()
#         assert connected
#
#         await communicator_0.send_json_to({
#             "function": "heartbeat",
#         })
#
#         response = await communicator_0.receive_json_from()
#         assert response['function'] == 'heartbeatconfirm'
#
#
#     async def test_add_channel(self):
#         communicator = WebsocketCommunicator(UserConsumer.as_asgi(), "/ws/")
#
#         connected, _ = await communicator.connect()
#         assert connected
#
#         await communicator.send_json_to({
#             "function": "add_channel",
#             'username': 'default'
#         })
#
#         assert await communicator.receive_nothing() is True
#
#
#     async def test_connect(self):
#         communicator = WebsocketCommunicator(UserConsumer.as_asgi(), "/ws/")
#
#         connected, _ = await communicator.connect()
#         assert connected
#
#     async def test

import json
from django.contrib.auth import get_user_model

from django.contrib.auth.models import User

from Chat.consumers import UserConsumer
from django.test import TestCase

from channels.testing import WebsocketCommunicator
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait

USERNAME_0 = "test00"
PASSWORD_0 = "123456"
USERNAME_1 = "test01"
PASSWORD_1 = "123456"

class MyConsumerTestCase(TestCase):
    async def register(self, username, password):
        payload = {
            "username": username,
            "password": password
        }
        return await self.client.post("/user/register", data=payload, content_type="application/json")

    async def login(self,username, password, email=""):
        payload = {
            "username": username,
            "password": password,
            "email": email
        }
        return await self.client.post("/user/login", data=payload, content_type="application/json")

    async def test_consumer(self):
        communicator = WebsocketCommunicator(UserConsumer.as_asgi(), "/ws/")

        # 连接 WebSocket
        connected, _ = await communicator.connect()

        assert connected

        # 发送消息到 Consumer
        # await communicator.send_json_to({"username": USERNAME_0, "password": PASSWORD_0, "function": "confirm", "from": USERNAME_0, "to": USERNAME_1})

        # response = await communicator.receive_from()
        # assert response == "hello"

        await communicator.disconnect()

        """

        # 接收 Consumer 的响应
        response = await communicator.receive_json_from()

        # 断言响应是否符合预期
        self.assertEqual(response, {"type": "my_message", "content": "Hello world!"})

        # 发送消息到 Consumer
        await communicator.send_json_to({"type": "my_message", "content": "Goodbye world!"})

        # 接收 Consumer 的响应
        response = await communicator.receive_json_from()

        # 断言响应是否符合预期
        self.assertEqual(response, {"type": "my_message", "content": "Goodbye world!"})

        """

        await communicator.disconnect()
