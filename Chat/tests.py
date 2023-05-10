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

USERNAME_0 = "test00"
PASSWORD_0 = "123456"
USERNAME_1 = "test01"
PASSWORD_1 = "123456"

class MyConsumerTestCase(TestCase):
    @sync_to_async
    def register(self, username, password):
        payload = {
            "username": username,
            "password": password
        }
        return self.client.post("/user/register", data=payload, content_type="application/json")

    @sync_to_async
    def login(self,username, password, email=""):
        payload = {
            "username": username,
            "password": password,
            "email": email
        }
        return self.client.post("/user/login", data=payload, content_type="application/json")

    @pytest.mark.django_db(transaction=True)
    async def test_consumer(self):
        await self.register(USERNAME_0,PASSWORD_0)
        await self.register(USERNAME_1,PASSWORD_1)

        communicator_0 = WebsocketCommunicator(UserConsumer.as_asgi(), "/ws/")
        communicator_1 = WebsocketCommunicator(UserConsumer.as_asgi(), "/ws/")

        # 连接 WebSocket
        connected, _ = await communicator_0.connect()
        assert connected
        connected, _ = await communicator_1.connect()
        assert connected

        # 发送消息到 Consumer
        await communicator_0.send_json_to({
            "function": "add_channel",
            "username": USERNAME_0
        })
        await communicator_1.send_json_to({
            "function": "add_channel",
            "username": USERNAME_1
        })

        await communicator_0.send_json_to({
            "function": "heartbeat",
        })
        response = await communicator_0.receive_from()
        assert json.loads(response)["cur_user"] == USERNAME_0

        await communicator_1.send_json_to({
            "function": "heartbeat",
        })
        response = await communicator_1.receive_from()
        assert json.loads(response)["cur_user"] == USERNAME_1

        await communicator_0.send_json_to({
            "function": "apply",
            "username": USERNAME_0,
            'to': USERNAME_1,
            'from': USERNAME_0
        })

        await communicator_1.send_json_to({
            "function": "confirm",
            "username": USERNAME_1,
            'to': USERNAME_0,
            'from': USERNAME_1
        })

        response = await communicator_1.receive_from()
        assert response.json()["function"] == 'friendlist'

        await communicator_0.disconnect()

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

        await communicator_0.disconnect()
