from asgiref.sync import sync_to_async
from channels.exceptions import StopConsumer
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
from pprint import pprint
from channels.generic.websocket import AsyncWebsocketConsumer
import json
import time

from UserManage.models import IMUser
from FriendRelation.models import FriendList, Friend, AddList
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from Chat.models import *


from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async

CONSUMER_OBJECT_LIST = []
USER_NAME_LIST = []


async def modify_add_request_list_with_username(other_username, add_list, answer, mode=0):
    """
    mode = 0 : add_list.reply
    mode = 1 : add_list.apply
    """
    index = await search_ensure_false_request_index(other_username, add_list, mode=mode)
    if index == -1:
        return False
    if mode == 0:
        add_list.reply_answer[index] = answer  #
        add_list.reply_ensure[index] = True
    elif mode == 1:
        add_list.apply_answer[index] = answer  #
        add_list.apply_ensure[index] = True
    await sync_to_async(add_list.save)()
    return True


async def search_ensure_false_request_index(other_username, add_list, mode=0):
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

async def username_list_to_id_list(username_list):
    res_list = []

    for i in username_list:
        user = await sync_to_async(await sync_to_async(User.objects.filter)(username=i).first)()
        if not user is None:
            res_list.append(user.id)

    return res_list


async def id_list_to_username_list(id_list):
    res_list = []

    for i in id_list:
        user = await sync_to_async(await sync_to_async(User.objects.filter)(id=i).first)()
        if not user is None:
            res_list.append(user.username)

    return res_list


async def get_power(chatroom, username):
    user_id = (await sync_to_async(User.objects.get)(username=username)).id

    if user_id == chatroom.master_name:
        return 2
    elif user_id in chatroom.manager_list:
        return 1
    else:
        return 0


class UserConsumer(AsyncWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.cur_user = None
        self.chat_group_name = None

    ### COPY
    async def connect(self):

        # Chat Ver

        # print('kwargs =', self.scope['url_route']['kwargs'])
        # kw = self.scope['url_route']['kwargs']
        # print('channel_name=', self.channel_name)
        # # kwargs = {'room_name': 'lobby'}
        # # kwargs = {'friend_name': 'lobby'}
        #
        # # self.channel_name= specific.3f537!273029f6116a45e191c37bcd8afb37c0
        #
        # if 'group_name' in kw.keys():
        #
        #     # chat_room = ChatRoom.objects.filter(chatroom_id=)
        #     self.group_name = self.scope["url_route"]["kwargs"]["group_name"]
        #     self.chat_group_name = "chat_" + self.group_name
        #
        #     await self.channel_layer.group_add(self.chat_group_name, self.channel_name)
        #
        #     print('group_name = ', self.group_name)
        #     print('chat_group_name = ', self.chat_group_name)
        #
        # elif 'friend_name' in kw.keys():
        #     self.friend_name = self.scope["url_route"]["kwargs"]["friend_name"]
        #     CHAT_OBJECT_LIST.append(self)

        CONSUMER_OBJECT_LIST.append(self)
        self.cur_user = await self.get_cur_username()
        await self.accept()

    async def get_cur_username(self):
        if self.cur_user is None:
            return self.scope['user'].username
        else:
            return self.cur_user

    async def receive(self, text_data=None, bytes_data=None):

        # Data
        # 1) self: self.scope/self.channel_name...
        # 2) text_data: original data from frontend

        json_info = json.loads(text_data)

        # fetch and init data
        function = json_info["function"]
        kw = self.scope['url_route']['kwargs']

        # original function zone

        if function == 'heartbeat':
            await self.heat_beat()

        elif function == 'apply':
            await self.apply_friend(text_data)

        elif function == 'confirm':
            await self.confirm_friend(json_info)

        elif function == 'decline':
            await self.decline_friend(json_info)

        elif function == 'fetchapplylist':
            await self.fetch_apply_list(json_info)

        elif function == 'fetchreceivelist':
            await self.fetch_reply_list(json_info)

        elif function == 'fetchfriendlist':
            await self.fetch_friend_list(json_info)

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
            await self.appoint_manager(json_info)

        elif function == 'transfer_master':
            await self.transfer_master(json_info)

        elif function == 'remove_group_member':
            await self.remove_group_member(json_info)

        elif function == "fetchroom":
            await self.fetch_room(json_info)

        elif function == "fetchmessage":
            await self.fetch_message(json_info)
    async def heat_beat(self):
        await self.send(text_data=json.dumps(
            {
                'function': 'heartbeatconfirm'
            }
        )
        )

    async def apply_friend(self, text_data):
        json_info = json.loads(text_data)
        username = json_info['username']
        user_model = get_user_model()
        user = await sync_to_async(user_model.objects.get)(username=username)
        im_user = await sync_to_async(IMUser.objects.get)(user=user)
        apply_from = json_info['from']
        apply_to = json_info['to']
        applyer_add_list = await sync_to_async(AddList.objects.get)(user_name=apply_from)
        receiver_add_list = await sync_to_async(AddList.objects.get)(user_name=apply_to)

        if not await search_ensure_false_request_index(apply_to, applyer_add_list, mode=1) == -1:
            # 确保被回复前不能重复发送
            # mode=1意为在applyer_add_list.applylist中寻找apply_to
            await self.send(text_data="Has Been Sent")
        elif apply_to in (await sync_to_async(FriendList.objects.get)(user_name=apply_from)).friend_list:
            await self.send(text_data="Is Already a Friend")
        else:
            applyer_add_list.apply_list.append(apply_to)
            applyer_add_list.apply_answer.append(False)
            applyer_add_list.apply_ensure.append(False)
            await sync_to_async(applyer_add_list.save)()

            receiver_add_list.reply_list.append(apply_from)
            receiver_add_list.reply_answer.append(False)
            receiver_add_list.reply_ensure.append(False)
            await sync_to_async(receiver_add_list.save)()

            # 若receiver在线申请发送到receiver

            add_list = await sync_to_async(AddList.objects.get)(user_name=username)
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
                if user.cur_user == apply_to:
                    await user.send(text_data=json.dumps(
                        {
                            'function': 'applylist',
                            'applylist': return_field
                        }
                    )
                    )
                    await user.fetch_room(json.dumps({"username":user.cur_user}))
                    await user.fetch_friend_list(json.dumps({"username": user.cur_user}))
            await self.fetch_room(json.dumps({"username":username}))
            await self.fetch_friend_list(json.dumps({"username": username}))

    async def confirm_friend(self, json_info):
        username = json_info['username']
        # 修改数据库
        apply_from = json_info['from']
        apply_to = json_info['to']
        receiver_add_list = await sync_to_async(AddList.objects.get)(user_name=apply_to)
        applyer_add_list = await sync_to_async(AddList.objects.get)(user_name=apply_from)

        await modify_add_request_list_with_username(apply_from, receiver_add_list, True)
        await modify_add_request_list_with_username(apply_to, applyer_add_list, True, mode=1)

        friend_list1 = await sync_to_async(FriendList.objects.get)(user_name=username)
        friend_list1.friend_list.append(apply_from)
        await sync_to_async(friend_list1.save)()
        friend_list2 = await sync_to_async(FriendList.objects.get)(user_name=apply_from)
        friend_list2.friend_list.append(username)
        await sync_to_async(friend_list2.save)()

        friend1 = Friend(user_name=username,
                         friend_name=apply_from,
                         group_name=friend_list1.group_list[0])
        friend2 = Friend(user_name=apply_from,
                         friend_name=username,
                         group_name=friend_list2.group_list[0])
        await sync_to_async(friend1.save)()
        await sync_to_async(friend2.save)()
        new_room = ChatRoom(mem_list=[],not_read=[],is_notice=[],is_top=[],manager_list=[],mes_list=[],notice_list=[])
        new_room.mem_list.append(username)
        new_room.not_read.append(0)
        new_room.mem_list.append(apply_from)
        new_room.not_read.append(0)
        await sync_to_async(new_room.save)()
        # 若applyer在线结果发送到applyer
        return_field = {"function": "confirm"}
        await self.send(text_data=json.dumps(return_field))

    async def decline_friend(self, json_info):
        # 修改数据库
        apply_from = json_info['from']
        apply_to = json_info['to']
        receiver_add_list = await sync_to_async(AddList.objects.get)(user_name=apply_to)
        applyer_add_list = await sync_to_async(AddList.objects.get)(user_name=apply_from)

        await modify_add_request_list_with_username(apply_from, receiver_add_list, False)
        await modify_add_request_list_with_username(apply_to, applyer_add_list, False, mode=1)

        return_field = {"function": "decline"}
        await self.send(text_data=json.dumps(return_field))

    async def fetch_apply_list(self, json_info):
        username = json_info['username']
        await self.fetch_addlist_attribute(username, 'applylist')

    async def fetch_reply_list(self, json_info):
        username = json_info['username']
        await self.fetch_addlist_attribute(username, 'receivelist')

    async def fetch_addlist_attribute(self, username, attribute_name):
        add_list = await sync_to_async(AddList.objects.get)(user_name=username)
        return_field = []

        if attribute_name == 'applylist':
            current_list = add_list.apply_list
            answer = add_list.apply_answer
            ensure = add_list.apply_ensure
        else:
            current_list = add_list.reply_list
            answer = add_list.reply_answer
            ensure = add_list.reply_ensure

        for li in range(len(current_list)):
            return_field.append(
                {
                    "username": current_list[li],
                    "is_confirmed": answer[li],
                    "make_sure": ensure[li]
                }
            )
        await self.send(text_data=json.dumps({
            'function': attribute_name,
            attribute_name: return_field
        }))

    async def disconnect(self, code):
        # Leave room group
        kw = self.scope['url_route']['kwargs']

        # if 'group_name' in kw.keys():
        #     await self.channel_layer.group_discard(self.chat_group_name, self.channel_name)
        # elif 'friend_name' in kw.keys():
        #     CHAT_OBJECT_LIST.remove(self)
        #     raise StopConsumer()

        CONSUMER_OBJECT_LIST.remove(self)
        raise StopConsumer()

        # Clients.objects.filter(channel_name=self.channel_name).delete()

    async def private_diffuse(self, event):
        message = event["message"]

        print('event in private_msg =', event)

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

        user_name = self.curuser
        # user_name = 'user'

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

        # user_name = 'user'
        user_name = self.curuser

        onliner = await database_sync_to_async(OnlineUser.objects.filter)(user_name=user_name).first()
        if onliner is None:
            self.send(text_data="you are not online")
            self.close()

        await database_sync_to_async(onliner.delete)()
        await database_sync_to_async(onliner.save)()

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

    async def find_chatroom(self, function_name, chatroom_id):
        chatroom = await sync_to_async(await sync_to_async(ChatRoom.objects.filter)(chatroom_id=chatroom_id).first)()

        if chatroom is None:
            await self.send(text_data=json.dumps({
                'function': function_name,
                'message': 'Group not found'
            }))

        return chatroom

    async def check_chatroom_master(self, function_name, chatroom, username):
        if chatroom.master_name != username:
            await self.send(text_data=json.dumps({
                'function': function_name,
                'message': 'You are not the group master'
            }))
            return False
        return True

    async def check_user_exist(self, function_name, username, message='User not found'):
        manager_user = await sync_to_async((await sync_to_async(User.objects.filter)(username=username)).first)()

        if manager_user is None:
            await self.send(text_data=json.dumps({
                'function': function_name,
                'message': message
            }))
        return manager_user

    async def check_user_in_chatroom(self, function_name, chatroom, username, message='User is not in the group'):
        user_id = (await sync_to_async(User.objects.get)(username=username)).id
        if user_id in chatroom.mem_list:
            return True
        else:
            await self.send(text_data=json.dumps({
                'function': function_name,
                'message': message
            }))
            return False

    async def create_group(self, json_info):
        """
        json_info =
        {
            'selection': 'list_create',
            'member_list': ['A', 'B'],
            'member_list':['A', 'B'],
            'room_name': 'lob',
        }
        """
        room_name = json_info['room_name']
        member_list = json_info['member_list']
        username = await self.get_cur_username()

        chat_room = create_chatroom(room_name, await username_list_to_id_list(member_list), username)
        chat_time_line = create_chat_timeline()
        chat_room.timeline_id = chat_time_line.timeline_id
        chat_time_line.chatroom_id = chat_room.chatroom_id
        await sync_to_async(chat_room.save)()
        await sync_to_async(chat_time_line.save)()

        await self.send(text_data=json.dumps({
            'function': 'create_group',
            'chatroom_id': chat_room.chatroom_id
        }))

    async def delete_group(self, json_info):
        """json_info =
        {
            'chatroom_id': 114514,
        }
        """
        function_name = 'delete_group'

        chatroom_id = json_info['chatroom_id']
        chatroom = await self.find_chatroom(function_name, chatroom_id)

        if not chatroom is None:
            username = await self.get_cur_username()

            if await self.check_chatroom_master(function_name, chatroom, username):
                chat_timeline = await sync_to_async(ChatTimeLine.objects.get)(chatroom.timeline_id)
                chatroom.delete()
                chat_timeline.delete()

                await self.send(text_data=json.dumps({
                    'function': function_name,
                    'message': 'Success'
                }))

    async def appoint_manager(self, json_info):
        """json_info =
        {
            'chatroom_id': 114514,
            'manager_name': 'ashitemaru'
        }
        """

        function_name = 'appoint_manager'

        chatroom_id = json_info['chatroom_id']
        chatroom = await self.find_chatroom(function_name, chatroom_id)

        if not chatroom is None:
            username = await self.get_cur_username()
            manager_name = json_info['manager_name']

            if await self.check_chatroom_master(function_name, chatroom, username):
                manager_user = await self.check_user_exist(function_name, manager_name)

                if not manager_user is None and \
                        await self.check_user_in_chatroom(function_name, chatroom, manager_name):
                    manager_user_id = manager_user.id
                    if manager_user_id in chatroom.manager_list:
                        await self.send(text_data=json.dumps({
                            'function': function_name,
                            'message': 'User is already an manager'
                        }))
                    else:
                        chatroom.manager_list.append(manager_user_id)
                        await self.send(text_data=json.dumps({
                            'function': function_name,
                            'message': 'Success'
                        }))

    async def transfer_master(self, json_info):
        """json_info =
        {
            'chatroom_id': 114514,
            'new_master_name': 'ashitemaru'
        }
        """
        function_name = 'transfer_master'

        chatroom_id = json_info['chatroom_id']
        chatroom = await self.find_chatroom(function_name, chatroom_id)

        if not chatroom is None:
            username = await self.get_cur_username()

            if await self.check_chatroom_master(function_name, chatroom, username):
                new_master_name = json_info['new_master_name']

                new_master = await self.check_user_exist(function_name, new_master_name)
                if not new_master is None and \
                        await self.check_user_in_chatroom(function_name, chatroom, new_master_name):
                    chatroom.master_name = new_master_name
                    await self.send(text_data=json.dumps({
                        'function': function_name,
                        'message': 'Success'
                    }))

    async def release_notice(self):
        pass

    async def remove_group_member(self, json_info):
        """json_info =
        {
            'chatroom_id': 114514,
            'member_name': 'ashitemaru'
        }
        """
        function_name = 'remove_group_member'

        chatroom_id = json_info['chatroom_id']
        chatroom = await self.find_chatroom(function_name, chatroom_id)

        if not chatroom is None:
            username = await self.get_cur_username()
            member_name = json_info['member_name']

            user = await self.check_user_exist(function_name, username)
            member = await self.check_user_exist(function_name, member_name, message='Member not found')

            if not user is None and not member is None and \
                    await self.check_user_in_chatroom(function_name, chatroom, username) and \
                    await self.check_user_in_chatroom(function_name, chatroom, member_name,
                                                      message='Member is not in the group'):

                user_power = await get_power(chatroom, username)
                member_power = await get_power(chatroom, member_name)

                if user_power - member_power <= 0:
                    await self.send(text_data=json.dumps({
                        'function': function_name,
                        'message': 'Permission denied'
                    }))
                else:
                    chatroom.manager_list.remove(member.id)
                    await sync_to_async(chatroom.save)()
                    await self.send(text_data=json.dumps({
                        'function': function_name,
                        'message': 'Success'
                    }))

    async def withdraw_message(self):
        pass

    async def fetch_friend_list(self, json_info):
        attribute_name = 'friendlist'

        username = json_info["username"]

        flist = await sync_to_async(FriendList.objects.get)(user_name=username)

        return_list = []
        flist_len = len(flist.group_list)

        for i in range(flist_len):
            return_list.append({
                "groupname": flist.group_list[i],
                "username": []
            })
            for friend_name in flist.friend_list:
                friend_list_tem = await sync_to_async(Friend.objects.filter)(friend_name=friend_name, user_name=username)
                friend = await sync_to_async(friend_list_tem.first)()
                if flist.group_list[i] == friend.group_name:
                    return_list[i]['username'].append(friend_name)

        await self.send(text_data=json.dumps({
            'function': attribute_name,
            attribute_name: return_list,
        }))

    async def fetch_room(self,json_info):
        username = json_info['username']
        return_field = []
        async for room in ChatRoom.objects.all():
            for li,user in enumerate(room.mem_list):
                if user == username:
                    return_field.append({
                        "roomid":room.chatroom_id,
                        "roomname":room.room_name,
                        "unreadnum":room.not_read[li],
                        "is_private":room.is_private
                    })
                    break
        await self.send(text_data=json.dumps({
            "function":"fetchroom",
            "roomlist":return_field
        }))

    async def fetch_message(self,json_info):
        chatroom_id = json_info['chatroom_id']
        username = json_info['username']
        room1 = await sync_to_async(ChatRoom.objects.filter)(chatroom_id=chatroom_id)
        room = await sync_to_async(room1.first)()
        return_field = []
        for li,user in enumerate(room.mem_list):
            if user == username:
                room.not_read[li] = 0
                await sync_to_async(room.save)()
                break
        for msg in room.mes_list:
            cur_message1 = await sync_to_async(Message.objects.filter)(msg_id=msg)
            cur_message = await sync_to_async(cur_message1.first)()
            return_field.append({
                "body":cur_message.body,
                "id":cur_message.msg_id,
                "time":cur_message.time,
                "sender":cur_message.sender
            })

        await self.send(text_data=json.dumps({
            "function":"fetchmessage",
            "messagelist":return_field
        }))