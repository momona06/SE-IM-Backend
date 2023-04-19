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
from consumers import ChatConsumer

class MyConsumerTestCase(TestCase):

    async def test_my_consumer(self):
        # 创建一个 WebsocketCommunicator 实例
        communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), "/ws/")

        # 连接 WebSocket
        connected, _= await communicator.connect()

        # 发送消息到 Consumer
        await communicator.send_json_to({"type": "my_message", "content": "Hello world!"})

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

        # 关闭 WebSocket 连接
        await communicator.disconnect()
