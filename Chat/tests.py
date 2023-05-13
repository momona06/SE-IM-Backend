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

    @pytest.mark.asyncio
    async def test_heartbeat(self):
        await self.register(USERNAME_0, PASSWORD_0)

        communicator_0 = WebsocketCommunicator(UserConsumer.as_asgi(), "/ws/")

        # 连接 WebSocket
        connected, _ = await communicator_0.connect()
        assert connected

        await communicator_0.send_json_to({
            "function": "heartbeat",
        })

        response = await communicator_0.receive_json_from()
        assert response['function'] == 'heartbeatconfirm'

        await communicator_0.disconnect()
