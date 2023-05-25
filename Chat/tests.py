from Chat.consumers import UserConsumer
from django.test import TestCase
from channels.testing import WebsocketCommunicator


USERNAME_0 = "test00"
PASSWORD_0 = "123456"
USERNAME_1 = "test01"
PASSWORD_1 = "123456"


class UserConsumerTest(TestCase):

    async def test_add_channel(self):
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



