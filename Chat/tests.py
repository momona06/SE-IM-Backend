import json

import pytest
from asgiref.sync import sync_to_async
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

from utils.utils_database import *

USERNAME_0 = "test00"
PASSWORD_0 = "123456"
USERNAME_1 = "test01"
PASSWORD_1 = "123456"


class MyConsumerTestCase(TestCase):
    @sync_to_async
    def register(self, username, password):
        tem = User.objects.create_user(username=username, password=password)
        tem.save()

        tem_user = User.objects.create_user(username=username, password=password)

        group = ['我的好友']
        friend_list = FriendList(user_name=username, group_list=group, friend_list=list())
        friend_list.save()

        add_list = AddList(user_name=username,
                               reply_list=list(), reply_answer=list(), reply_ensure=list(),
                               apply_list=list(), apply_answer=list(), apply_ensure=list())
        add_list.save()

    # @sync_to_async
    # def login(self, username, password, email=""):
    #     payload = {
    #         "username": username,
    #         "password": password,
    #         "email": email
    #     }
    #     return self.client.post("/user/login", data=payload, content_type="application/json")

    @pytest.mark.django_db(transaction=True)
    async def test_consumer(self):
        await self.register(USERNAME_0, PASSWORD_0)
        await self.register(USERNAME_1, PASSWORD_1)

        user = await sync_to_async(User.objects.get)(username=USERNAME_0)

        print(user.password)

        addlist = await sync_to_async(AddList.objects.get)(username=USERNAME_0)
        print(addlist)

        communicator_0 = WebsocketCommunicator(UserConsumer.as_asgi(), "/ws/")

        # 连接 WebSocket
        connected, _ = await communicator_0.connect()
        assert connected

        # 发送消息到 Consumer
        await communicator_0.send_json_to({
            "function": "add_channel",
            "username": USERNAME_0
        })

        await communicator_0.send_json_to({
            "function": "heartbeat",
        })
        response = await communicator_0.receive_from()
        assert json.loads(response)["cur_user"] == USERNAME_0

        await communicator_0.send_json_to({
            "function": "heartbeat",
        })
        response = await communicator_0.receive_from()
        assert json.loads(response)["cur_user"] == USERNAME_0

        # await communicator_0.disconnect()
        await communicator_0.send_json_to({
            "function": "apply",
            "username": USERNAME_0,
            'to': USERNAME_1,
            'from': USERNAME_0
        })
        addlist = await sync_to_async(AddList.objects.get)(username=USERNAME_0)
        print(addlist)

        communicator_1 = WebsocketCommunicator(UserConsumer.as_asgi(), "/ws/")

        connected, _ = await communicator_1.connect()
        assert connected
        await communicator_1.send_json_to({
            "function": "add_channel",
            "username": USERNAME_1
        })

        await communicator_1.send_json_to({
            "function": "heartbeat",
        })
        response = await communicator_1.receive_from()
        assert json.loads(response)["cur_user"] == USERNAME_1

        await communicator_1.send_json_to({
            "function": "confirm",
            "username": USERNAME_1,
            'to': USERNAME_0,
            'from': USERNAME_1
        })


        # await communicator_1.disconnect()

        """

        # 接收 Consumer 的响应
        response = await communicator_0.receive_json_from()

        # 断言响应是否符合预期
        self.assertEqual(response, {"type": "my_message", "content": "Hello world!"})

        # 发送消息到 Consumer
        await communicator_0.send_json_to({"type": "my_message", "content": "Goodbye world!"})

        # 接收 Consumer 的响应
        response = await communicator_0.receive_json_from()

        # 断言响应是否符合预期
        self.assertEqual(response, {"type": "my_message", "content": "Goodbye world!"})

        """
