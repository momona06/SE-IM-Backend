import json
from django.contrib.auth import get_user_model

from django.contrib.auth.models import User
from UserManage.models import IMUser
from django.test import TestCase

from channels.testing import ChannelsLiveServerTestCase,WebsocketCommunicator
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
    def register(self, username, password):
        payload = {
            "username": username,
            "password": password
        }
        return self.client.post("/user/register", data=payload, content_type="application/json")

    def login(self,username, password, email=""):
        payload = {
            "username": username,
            "password": password,
            "email": email
        }
        return self.client.post("/user/login", data=payload, content_type="application/json")

    async def test_consumer(self):
        # 创建一个 WebsocketCommunicator 实例
        # communicator = WebsocketCommunicator(FriendConsumer.as_asgi(), "/ws/")

        # 连接 WebSocket
        #connected, _ = await communicator.connect()

        # assert connected

        # 发送消息到 Consumer
        # await communicator.send_json_to({"username": USERNAME_0, "password": PASSWORD_0, "function": "confirm", "from": USERNAME_0, "to": USERNAME_1})

        # response = await communicator.receive_from()
        # assert response == "hello"

        # await communicator.disconnect()

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

        # 关闭 WebSocket 连接
        # await communicator.disconnect()
