from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from asyncio import *
from Chat.consumers import UserConsumer
from django.test import TestCase

from channels.testing import WebsocketCommunicator

from FriendRelation.models import FriendList, AddList

USERNAME_0 = "test00"
PASSWORD_0 = "123456"
USERNAME_1 = "test01"
PASSWORD_1 = "123456"


class UserConsumerTest(TestCase):
    def user_register(self, username, password):
        payload = {
            "username": username,
            "password": password
        }
        return self.client.post("/user/register", data=payload, content_type="application/json")

    def user_login(self, username, password, email=""):
        payload = {
            "username": username,
            "password": password,
            "email": email
        }
        return self.client.post("/user/login", data=payload, content_type="application/json")

    def user_check(self, my_username, check_name, token):
        payload = {
            "my_username": my_username,
            "check_name": check_name,
            "token": token,
        }
        return self.client.post("/friend/checkuser", data=payload, content_type="application/json")

    def user_search(self, my_username, search_username):
        payload = {
            "my_username": my_username,
            "search_username": search_username,
        }
        return self.client.post("/friend/searchuser", data=payload, content_type="application/json")

    def user_logout(self, username, token):
        payload = {
            "username": username,
            "token": token
        }
        return self.client.delete("/user/logout", data=payload, content_type="application/json")

    def user_cancel(self, username, input_password):
        payload = {
            "username": username,
            "input_password": input_password
        }
        return self.client.delete("/user/cancel", data=payload, content_type="application/json")

    # async def register(self, username, password):
    #     tem = await sync_to_async(User.objects.create_user)(username=username, password=password)
    #     await sync_to_async(tem.save)()
    #
    #     group = ['我的好友']
    #     friend_list = await sync_to_async(FriendList)(user_name=username, group_list=group, friend_list=list())
    #     await sync_to_async(friend_list.save)()
    #
    #     add_list = await sync_to_async(AddList)(user_name=username,
    #                                             reply_list=list(), reply_answer=list(), reply_ensure=list(),
    #                                             apply_list=list(), apply_answer=list(), apply_ensure=list())
    #     await sync_to_async(add_list.save)()
    #
    # async def test_heartbeat(self):
    #     communicator_0 = WebsocketCommunicator(UserConsumer.as_asgi(), "/wsconnect")
    #
    #     # 连接 WebSocket
    #     connected, _ = await communicator_0.connect()
    #     assert connected
    #
    #     await communicator_0.send_json_to({
    #         "function": "heartbeat",
    #     })
    #
    #     response = await communicator_0.receive_json_from()
    #     self.assertEqual(response['function'], 'heartbeatconfirm')

    async def test_add_channel(self):
        # res_reg = await sync_to_async(self.user_register)(USERNAME_0, PASSWORD_0)
        # res_lin = await sync_to_async(self.user_login)(USERNAME_0, PASSWORD_0)
        # self.assertEqual(res_reg.json()["code"], 0)
        # self.assertEqual(res_lin.json()["code"], 0)

        communicator = WebsocketCommunicator(UserConsumer.as_asgi(), "/wsconnect")

        connected, _ = await communicator.connect()
        self.assertEqual(connected, True)

        await communicator.send_json_to({
            "function": "add_channel",
            'username': 'default'
        })

        assert await communicator.receive_nothing() is True

        # await sync_to_async(self.user_logout)(USERNAME_0, PASSWORD_0)

    async def test_connect(self):
        communicator = WebsocketCommunicator(UserConsumer.as_asgi(), "/wsconnect")
        connected, _ = await communicator.connect()
        self.assertEqual(connected, True)

    async def test_create_group(self):
        communicator1 = WebsocketCommunicator(UserConsumer.as_asgi(), "/wsconnect")
        communicator2 = WebsocketCommunicator(UserConsumer.as_asgi(), "/wsconnect")

        await communicator1.send_json_to({
            "function": "add_channel",
            'username': 'user1'
        })

        assert await communicator1.receive_nothing() is True

        await communicator2.send_json_to({
            "function": "add_channel",
            'username': 'user2'
        })

        assert await communicator2.receive_nothing() is True

        await communicator1.send_json_to({
            "function": "create_group",
            "member_list": ['user1', 'user2'],
            "room_name": "GROUP"
        })

        assert await communicator1.receive_nothing() is True



