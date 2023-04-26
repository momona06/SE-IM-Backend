from channels.exceptions import StopConsumer
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
from pprint import *
import json
import time

from UserManage.models import IMUser, TokenPoll
from FriendRelation.models import FriendList, Friend, AddList
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model, authenticate
from Chat.models import *


from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async # TODO: Check

CONSUMER_OBJECT_LIST = []
USER_NAME_LIST = []


def modify_add_request_list_with_username(other_username, add_list, answer, mode=0):
    """
    mode = 0 : add_list.reply
    mode = 1 : add_list.apply
    """
    index = search_ensure_false_request_index(other_username, add_list, mode=mode)
    if index == -1:
        return False
    if mode == 0:
        add_list.reply_answer[index] = answer  #
        add_list.reply_ensure[index] = True
    elif mode == 1:
        add_list.apply_answer[index] = answer  #
        add_list.apply_ensure[index] = True
    add_list.save()
    return True


def search_ensure_false_request_index(other_username, add_list, mode=0):
    if mode == 0:
        for li, peo in enumerate(add_list.reply_list):
            if peo == other_username and not add_list.reply_ensure[li]:
                return li
    elif mode == 1:
        for li, peo in enumerate(add_list.apply_list):
            if peo == other_username and not add_list.apply_ensure[li]:
                return li
    return -1


# channel: the specific user
# group: a group of channels (users)

class UserConsumer(AsyncWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.curuser = None

    async def connect(self):

        print('session =', self.scope['session'])
        CONSUMER_OBJECT_LIST.append(self)

        self.curuser = self.scope['user'].username

        print('\nself.scope["user"] = ', self.scope['user'])
        print('\nself.curuser / self.scope["user"].username = ', self.curuser)
        await self.accept()

    async def receive(self, text_data):

        # Data
        # 1) self: self.scope/self.channel_name...
        # 2) text_data: original data from frontend

        json_info = json.loads(text_data)
        print('\njson_info =', json_info)
        function = json_info["function"]

        # original function zone

        if function == 'heartbeat':
            await self.heart_beat()

        elif function == 'apply':
            await self.apply_friend()

        elif function == 'confirm':
            await self.confirm_friend()

        elif function == 'decline':
            await self.decline_friend()

        elif function == 'fetchapplylist':
            await self.fetch_apply_list()

        elif function == 'fetchreplylist':
            await self.fetch_reply_list()


        # function zone

        elif function == 'add_chat':
            await self.add_chat(json_info)

        elif function == 'leave_chat':
            await self.leave_chat(json_info)

        elif function == 'send_message':
            await self.send_message(json_info)

        elif function == 'ack_message':
            await self.acknowledge_message(json_info)

        elif function == 'withdraw_message':
            await self.withdraw_message(json_info)

        elif function == 'create_group':
            await self.create_group(json_info)

        elif function == 'delete_group':
            await self.delete_group(json_info)

        elif function == 'appoint_manage':
            await self.appoint_manager()

        elif function == 'transfer_master':
            await self.transfer_master()

        elif function == 'remove_group_member':
            await self.remove_group_member()

    async def heart_beat(self):
        pass

    async def apply_friend(self):
        pass

    async def confirm_friend(self):
        pass

    async def decline_friend(self):
        pass

    async def fetch_apply_list(self):
        pass

    async def fetch_reply_list(self):
        pass

    async def disconnect(self):

        CONSUMER_OBJECT_LIST.remove(self)
        raise StopConsumer()


    # async def private_diffuse(self, event):
    #     message = event["message"]
    #
    #     print('event in private_msg =', event)
    #
    #     await self.send(text_data=json.dumps({
    #         "message": message
    #     }))

    async def message_diffuse(self, event):
        msg_body = event["msg_body"]
        msg_id = event["msg_id"]
        print('event in public_msg =', event)
        # event = {'type': 'chat_message', 'message': 'res'}

        await self.send(text_data=json.dumps({
            'type': 'Msg',
            'msg_id': msg_id,
            "msg_body": msg_body
        }))

    async def acknowledge_diffuse(self, event):

        msg_id = event["msg_id"]

        print('event in public_msg =', event)
        # event = {'type': 'chat_message', 'message': 'res'}

        await self.send(text_data=json.dumps({
            'type': 'Ack',
            'msg_id': msg_id,

        }))



    async def add_chat(self, json_info):
        '''
        json_info: {
            'chatroom_id': '5',
            'room_name': 'default',
            'is_private': True
        }

        json_info: {
            'chatroom_id': '8',
            'room_name': 'lobby',
            'is_private': False
        }
        '''

        # user_name = self.curuser
        user_name = 'user'

        user = await database_sync_to_async(User.objects.get)(username=user_name)
        im_user = await database_sync_to_async(IMUser.objects.get)(user=user)

        room_name = json_info['room_name']
        room_id = json_info['chatroom_id']
        is_private = json_info['is_private']

        new_onliner = await OnlineUser(user_name=user_name, channel_name=self.channel_name, chatroom_id=room_id)
        await new_onliner.save()

        chat_room = await database_sync_to_async(ChatRoom.objects.filter)(chatroom_id=room_id).first()
        if chat_room is None:
            await self.send(text_data="chatroom not exists")
            await self.close()

        self.group_name = json_info['room_name']
        self.chat_group_name = "chat_" + self.group_name + room_id

        await self.channel_layer.group_add(self.chat_group_name, self.channel_name)



    async def leave_chat(self, json_info):
        '''
        json_info: {
        }
        '''

        user_name = 'user'
        # user_name = self.curuser

        onliner = await database_sync_to_async(OnlineUser.objects.filter)(user_name=user_name).first()
        if onliner is None:
            self.send(text_data="you are not online")
            self.close()

        await database_sync_to_async(onliner.delete)()

        await self.channel_layer.group_discard(self.chat_group_name, self.channel_name)



    async def send_message(self, json_info):
        '''
        json_info: {
            'msg_type': 'text',
            'msg_body': 'hello',
            'ref_id': 16,
        }
        '''

        # Inspiration & Target
        # striked by Msg R1
        # send Ack 2(Msg 2) to cli A
        # send Msg R3 to cli B

        # append the timeline

        user_name = self.curuser

        onliner = await database_sync_to_async(OnlineUser.objects.filter)(user_name=user_name).first()
        if onliner is None:
            await self.send('you are not in the chatroom')
            await self.close()

        room_id = onliner.chatroom_id

        chatroom = await database_sync_to_async(ChatRoom.objects.filter)(chatroom_id=room_id).first()
        if chatroom is None:
            await self.send('chatroom not exists')
            await self.close()


        timeline = await database_sync_to_async(ChatTimeLine.objects.get)(chatroom_id=room_id)

        msg_type = json_info['msg_type']
        msg_body = json_info['msg_body']

        # ref_id = json_info['ref_id']
        msg_time = await sync_to_async(time.strftime)('%Y-%m-%d %H:%M:%S', time.localtime())
        message = await database_sync_to_async(create_message)(msg_type, msg_body, msg_time, user_name)

        msg_id = message.msg_id

        await sync_to_async(timeline.msg_line.append)(message.msg_id)

        #
        await self.channel_layer.group_send(
            self.chat_group_name,
            {
                "type": "message_diffuse",
                'msg_id': msg_id,
                'msg_body': msg_body,
            }
        )

        #
        await self.send(
            text_data=json.dumps(
            {
                "type": "acknowledge_diffuse",
                'msg_id': msg_id,
            }
            )
        )

        # for member in chatroom.mem_list:
        #     online_member = await database_sync_to_async(OnlineUser.objects.filter)(user_name=member).first()
        #     if online_member is None:


    async def acknowledge_message(self, json_info):
        '''
        json_info: {
            'msg_id': 16,
        }
        '''

        # Inspiration & Target
        # striked by Ack 4
        # send Ack 5 to cli B
        ### delete:[send Ack 6 to cli A]

        # move the cursor


        user_name = self.curuser
        # user_name = 'user'

        msg_id = json_info['msg_id']
        sender = json_info['sender']

        message = await database_sync_to_async(Message.objects.filter)(msg_id=msg_id).first()
        if message is None:
            await self.send('message not exists')
            await self.close()

        if message.sender != sender:
            await self.send('sender not match')
            await self.close()

        room_id = message.chatroom_id

        chatroom = await database_sync_to_async(ChatRoom.objects.filter)(chatroom_id=room_id).first()
        if chatroom is None:
            await self.send('chatroom not exists')
            await self.close()

        timeline = await database_sync_to_async(ChatTimeLine.objects.filter)(chatroom_id=room_id).first()

        lis = 0
        for li, mem_name in enumerate(chatroom.mem_list):
            if mem_name == user_name:
                lis = li
                break

        timeline.cursor_list[lis] += 1


        await self.send(
            text_data=json.dumps(
            {
                "type": "acknowledge_diffuse",
                'msg_id': msg_id,
            }
            )
        )


    async def create_group(self, json_info):
        """
        json_info =
        {
            'selection': 'list_create',
            'member_list': ['A', 'B'],
            'room_name': 'lob',
        }
        """
        room_name = json_info['room_name']
        member_list = json_info['member_list']
        selection = json_info['selection']
        if selection == 'list_create':

            chat_room = create_chatroom()
            chat_time_line = create_chat_timeline()
            chat_room.timeline_id = chat_time_line.timeline_id
            chat_time_line.chatroom_id = chat_room.chatroom_id
            chat_room.save()
            chat_time_line.save()

        elif selection == 'based_create':
            pass

    async def delete_group(self, json_info):
        pass

    async def appoint_manager(self):
        pass

    async def transfer_master(self):
        pass

    async def release_notice(self):
        pass

    async def remove_group_member(self):
        pass

    async def withdraw_message(self):
        pass

















'''
NOT WORK
'''

'''
class FriendConsumer(WebsocketConsumer):
    # self看作当前触发事件的客户端

    def websocket_token_check(self, user_token, token):
        if user_token != token:
            self.close()

    def connect(self):
        """
        客户端浏览器发来连接请求之后触发，对应ws.onopen()
        """

        # message: 前端调用send发送的Json信息触发receive，dict格式
        # self：连接的客户端的数据结构
        # self.send()：发送信息到客户端触发onmessage函数，可以发送json信息
        # self.scope: 本次连接的基本信息，dict格式

        CONSUMER_OBJECT_LIST.append(self)
        self.curuser = self.scope['user'].username
        # 服务端接收连接，向客户端浏览器发送一个加密字符串
        self.accept()
        # USER_NAME_LIST.append(username)

    def receive(self, text_data):
        """
        客户端浏览器向服务端发送消息，对应ws.send()
        """

        # print(type(message))
        # print(type(message['text']))
        # print(message['text'])
        # pprint(message)

        # message = json.loads(message['text'])
        # function = message['function']

        json_info = json.loads(text_data)
        function = json_info['function']

        if json_info['function'] == 'heartbeat':
            self.send(text_data=json.dumps(
                {
                    'function': 'heartbeatconfirm'
                }
            )
            )

        else:
            username = json_info['username']
            function = json_info['function']

            user_model = get_user_model()
            user = user_model.objects.get(username=username)
            im_user = IMUser.objects.get(user=user)

            if function == 'apply':
                # 修改数据库
                apply_from = json_info['from']
                apply_to = json_info['to']
                applyer_add_list = AddList.objects.get(user_name=apply_from)
                receiver_add_list = AddList.objects.get(user_name=apply_to)

                if not search_ensure_false_request_index(apply_to, applyer_add_list, mode=1) == -1:
                    # 确保被回复前不能重复发送
                    # mode=1意为在applyer_add_list.applylist中寻找apply_to
                    self.send(text_data="Has Been Sent")
                elif apply_to in FriendList.objects.get(user_name=apply_from).friend_list:
                    self.send(text_data="Is Already a Friend")
                else:
                    applyer_add_list.apply_list.append(apply_to)
                    applyer_add_list.apply_answer.append(False)
                    applyer_add_list.apply_ensure.append(False)
                    applyer_add_list.save()

                    receiver_add_list.reply_list.append(apply_from)
                    receiver_add_list.reply_answer.append(False)
                    receiver_add_list.reply_ensure.append(False)
                    receiver_add_list.save()

                    # 若receiver在线申请发送到receiver

                    add_list = AddList.objects.get(user_name=username)
                    return_field = []
                    flen = len(add_list.apply_list)
                    for li in range(flen):
                        return_field.append(
                            {
                                "username": add_list.apply_list[li],
                                "is_confirmed": add_list.apply_answer[li],
                                "make_sure": add_list.apply_ensure[li]
                            }
                        )
                    for user in CONSUMER_OBJECT_LIST:
                        if user.curuser == apply_to:
                            user.send(text_data=json.dumps(
                                {
                                    'function': 'applylist',
                                    'applylist': return_field
                                }
                            )
                            )

            elif function == 'confirm':
                # 修改数据库
                apply_from = json_info['from']
                apply_to = json_info['to']
                receiver_add_list = AddList.objects.get(user_name=apply_to)
                applyer_add_list = AddList.objects.get(user_name=apply_from)

                modify_add_request_list_with_username(apply_from, receiver_add_list, True)
                modify_add_request_list_with_username(apply_to, applyer_add_list, True, mode=1)

                friend_list1 = FriendList.objects.get(user_name=username)
                friend_list1.friend_list.append(apply_from)
                friend_list1.save()
                friend_list2 = FriendList.objects.get(user_name=apply_from)
                friend_list2.friend_list.append(username)
                friend_list2.save()

                friend1 = Friend(user_name=username,
                                 friend_name=apply_from,
                                 group_name=friend_list1.group_list[0])
                friend2 = Friend(user_name=apply_from,
                                 friend_name=username,
                                 group_name=friend_list2.group_list[0])
                friend1.save()
                friend2.save()
                # 若applyer在线结果发送到applyer
                return_field = {"function": "confirm"}
                self.send(text_data=json.dumps(return_field))

            elif function == 'decline':
                # 修改数据库
                apply_from = json_info['from']
                apply_to = json_info['to']
                receiver_add_list = AddList.objects.get(user_name=apply_to)
                applyer_add_list = AddList.objects.get(user_name=apply_from)

                modify_add_request_list_with_username(apply_from, receiver_add_list, False)
                modify_add_request_list_with_username(apply_to, applyer_add_list, False, mode=1)

                return_field = {"function": "decline"}
                self.send(text_data=json.dumps(return_field))

            elif function == 'fetchapplylist':
                add_list = AddList.objects.get(user_name=username)
                return_field = []
                flen = len(add_list.apply_list)
                for li in range(flen):
                    return_field.append(
                        {
                            "username": add_list.apply_list[li],
                            "is_confirmed": add_list.apply_answer[li],
                            "make_sure": add_list.apply_ensure[li]
                        }
                    )
                self.send(text_data=json.dumps({
                    'function': 'applylist',
                    'applylist': return_field
                }
                )
                )
                # 发送list到client

            elif function == 'fetchreceivelist':
                add_list = AddList.objects.get(user_name=username)
                return_field = []
                flen = len(add_list.reply_list)
                for li in range(flen):
                    return_field.append(
                        {
                            "username": add_list.reply_list[li],
                            "is_confirmed": add_list.reply_answer[li],
                            "make_sure": add_list.reply_ensure[li]
                        }
                    )
                self.send(text_data=json.dumps(
                    {
                        'function': 'receivelist',
                        'receivelist': return_field
                    }
                )
                )
                # 发送list到client

            else:
                self.send(text_data=function + "Unknown Function")


def disconnect(self):
    """
    客户端浏览器主动断开连接，对应ws.onclose()
    """

    # USER_NAME_LIST.remove(username)

    CONSUMER_OBJECT_LIST.remove(self)
    raise StopConsumer()
'''