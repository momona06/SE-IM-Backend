from channels.exceptions import StopConsumer
from channels.generic.websocket import AsyncWebsocketConsumer
import json
import time

from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
from django.contrib.auth.models import User

from Chat.models import create_chatroom, create_onlineuser, create_message, ChatRoom, Message
from FriendRelation.models import FriendList, Friend
from utils.utils_database import *

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


async def username_list_to_id_list(username_list):
    res_list = []

    for i in username_list:
        user_list_tem = await sync_to_async(User.objects.filter)(username=i)
        user = await sync_to_async(user_list_tem.first)()
        if user is not None:
            res_list.append(user.id)

    return res_list


async def id_list_to_username_list(id_list):
    res_list = []

    for i in id_list:
        user_list_tem = await sync_to_async(User.objects.filter)(id=i)
        user = await sync_to_async(user_list_tem.first)()
        if user is not None:
            res_list.append(user.username)

    return res_list


async def get_power(chatroom, username):
    user_id = await get_user_id(username)

    if user_id == chatroom.master_name:
        return 2
    elif user_id in chatroom.manager_list:
        return 1
    else:
        return 0


# channel: the specific user
# group: a group of channels (users)

class UserConsumer(AsyncWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.cur_user = None
        self.chat_group_name = None

    async def connect(self):
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
        function = json_info["function"]

        # friendlist zone
        if function == 'heartbeat':
            await self.heat_beat()

        elif function == 'apply':
            await self.apply_friend(json_info)

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

        # chat zone

        # 连接私聊/群聊
        elif function == 'add_chat':
            await self.add_chat(json_info)

        # 断开私聊/群聊连接
        elif function == 'leave_chat':
            await self.leave_chat(json_info)

        # 发送各种消息
        # {text}: 直接处理
        # {rel}: 添加
        # {image, audio, file}: 采用下载链接处理
        elif function == 'send_message':
            await self.send_message(json_info)

        # 确认收到消息
        elif function == 'ack_message':
            await self.acknowledge_message(json_info)

        # 撤回自己的消息
        elif function == 'withdraw_message':
            await self.withdraw_message(json_info)

        # 创建群聊
        elif function == 'create_group':
            await self.create_group(json_info)

        # 群主删除群聊
        elif function == 'delete_group':
            await self.delete_group(json_info)

        # 申请加入群聊
        elif function == 'add_group':
            await self.add_group(json_info)

        # 用户自己退出群聊
        elif function == 'leave_group':
            await self.leave_group(json_info)

        # 群主任命管理员
        elif function == 'appoint_manage':
            await self.appoint_manager(json_info)

        # 群主转让
        elif function == 'transfer_master':
            await self.transfer_master(json_info)

        # 群主/管理员允许申请用户加入群聊
        elif function == 'allow_add_group':
            await self.allow_add_group(json_info)

        # 群主/管理员直接添加用户到群聊
        elif function == 'add_group_member':
            await self.add_group_member(json_info)

        # 群主/管理员移除群成员
        elif function == 'remove_group_member':
            await self.remove_group_member(json_info)

        # 获取用户的所有私聊/群聊信息
        elif function == "fetch_room":
            await self.fetch_room(json_info)

        elif function == "fetch_roominfo":
            await self.fetch_roominfo(json_info)

        # 获取群消息列表
        elif function == "fetch_message":
            await self.fetch_message(json_info)

        # 发送群公告
        elif function == "release_notice":
            await self.release_notice(json_info)

    async def heat_beat(self):
        await self.send(text_data=json.dumps({
            'function': 'heartbeatconfirm'
        }))

    async def apply_friend(self, json_info):
        username = json_info['username']
        apply_from = json_info['from']
        apply_to = json_info['to']
        applyer_add_list = await filter_first_addlist(apply_from)
        receiver_add_list = await filter_first_addlist(apply_to)

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

            add_list = await get_addlist(username)
            return_field = []
            flen = len(add_list.apply_list)
            for li in range(flen):
                return_field.append({
                        "username": add_list.apply_list[li],
                        "is_confirmed": add_list.apply_answer[li],
                        "make_sure": add_list.apply_ensure[li]
                })
            for user in CONSUMER_OBJECT_LIST:
                if user.cur_user == apply_to:
                    await user.send(text_data=json.dumps({
                            'function': 'applylist',
                            'applylist': return_field
                    }))

    async def confirm_friend(self, json_info):
        username = json_info['username']
        # 修改数据库
        apply_from = json_info['from']
        apply_to = json_info['to']
        receiver_add_list = await get_addlist(apply_to)
        applyer_add_list = await get_addlist(apply_from)

        await modify_add_request_list_with_username(apply_from, receiver_add_list, True)
        await modify_add_request_list_with_username(apply_to, applyer_add_list, True, mode=1)

        friend_list1 = await get_friendlist(username)
        friend_list1.friend_list.append(apply_from)
        await sync_to_async(friend_list1.save)()
        friend_list2 = await get_friendlist(apply_from)
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

        await create_chatroom('private_chat', [username, apply_from], username, is_private=True)

        # 若applyer在线结果发送到applyer
        return_field = {"function": "confirm"}
        await self.send(text_data=json.dumps(return_field))
        for user in CONSUMER_OBJECT_LIST:
            if user.cur_user == apply_to:
                # await user.fetch_room(json.dumps({"username": user.cur_user}))
                await user.fetch_friend_list({"username": user.cur_user})
                break


        # await self.fetch_room(json.dumps({"username": username}))
        await self.fetch_friend_list({"username": username})
        await self.fetch_reply_list({"username": username})

    async def decline_friend(self, json_info):
        # 修改数据库
        apply_from = json_info['from']
        apply_to = json_info['to']
        receiver_add_list = await get_addlist(apply_to)
        applyer_add_list = await get_addlist(apply_from)

        await modify_add_request_list_with_username(apply_from, receiver_add_list, False)
        await modify_add_request_list_with_username(apply_to, applyer_add_list, False, mode=1)

        return_field = {"function": "decline"}
        await self.send(text_data=json.dumps(return_field))
        username = await self.get_cur_username()
        await self.fetch_reply_list({"username": username})

    async def fetch_apply_list(self, json_info):
        username = json_info['username']
        await self.fetch_addlist_attribute(username, 'applylist')

    async def fetch_reply_list(self, json_info):
        username = json_info['username']
        await self.fetch_addlist_attribute(username, 'receivelist')

    async def fetch_addlist_attribute(self, username, attribute_name):
        add_list = await get_addlist(username)
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
            return_field.append({
                    "username": current_list[li],
                    "is_confirmed": answer[li],
                    "make_sure": ensure[li]
            })
        await self.send(text_data=json.dumps({
            'function': attribute_name,
            attribute_name: return_field
        }))

    async def disconnect(self, code):

        CONSUMER_OBJECT_LIST.remove(self)
        raise StopConsumer()

        # Clients.objects.filter(channel_name=self.channel_name).delete()

    async def message_diffuse(self, event):
        msg_body = event["msg_body"]
        msg_id = event["msg_id"]

        # event = {'type': 'chat_message', 'message': 'res'}

        await self.send(text_data=json.dumps({
            'type': 'Msg',
            'msg_id': msg_id,
            "msg_body": msg_body
        }))

    async def acknowledge_diffuse(self, event):

        msg_id = event["msg_id"]

        # event = {'type': 'chat_message', 'message': 'res'}

        await self.send(text_data=json.dumps({
            'type': 'Ack',
            'msg_id': msg_id,
        }))

    async def add_chat(self, json_info):
        """
        json_info = {
            'chatroom_id': '5',
            'room_name': 'default',
            'is_private': True
        }
        """

        # 初始化
        user_name = self.cur_user
        room_name = json_info['room_name']
        room_id = json_info['chatroom_id']
        is_private = json_info['is_private']

        # 加入在线用户列表
        await sync_to_async(create_onlineuser)(user_name, self.channel_name, room_id)

        # 加入群聊
        chat_room = await filter_first_chatroom(chatroom_id=room_id)
        if chat_room is None:
            await self.send(text_data="chatroom not exists")
            await self.close()
        self.chatroom_name = "chat_" + room_name + room_id
        await self.channel_layer.group_add(self.chatroom_name, self.channel_name)

        # Fix: Unify
        # 发送历史信息
        # Msg R3 for back case
        # self.fetch_message(json_info)

    async def leave_chat(self, json_info):
        '''
        json_info: {}
        '''

        # 初始化
        user_name = self.cur_user
        onliner = await filter_first_onlineuser(user_name)

        # 改动Timeline的cursor
        chatroom = await filter_first_chatroom(chatroom_id=onliner.chatroom_id)
        timeline = await filter_first_timeline(timeline_id=chatroom.timeline_id)
        lis = chatroom.mem_list.index(user_name)
        timeline.cursor_list[lis] = 0

        # 离开在线用户列表
        if onliner is None:
            await self.send(text_data="you are not online")
            await self.close()
        await database_sync_to_async(onliner.delete)()
        await database_sync_to_async(onliner.save)()

        # 离开群聊
        self.chatroom_name = None
        await self.channel_layer.group_discard(self.chatroom_name, self.channel_name)

    async def send_message(self, json_info):
        '''
        json_info = {
            'msg_type': 'text',
            'msg_body': 'hello',
            'reply_id': 16,
        }

        '''

        # Pipeline
        # called by Msg R1
        # send Msg R3 to cli Bs
        # send Ack 2 to cli A
        # move the cursor of cli A

        # 初始化
        user_name = self.cur_user

        # 获取在线用户
        onliner = await filter_first_onlineuser(user_name)
        if onliner is None:
            await self.send('you are not in the chatroom')
            await self.close()

        # 获取群聊和Timeline
        room_id = onliner.chatroom_id
        chatroom = await filter_first_chatroom(chatroom_id=room_id)
        if chatroom is None:
            await self.send('chatroom not exists')
            await self.close()
        timeline = await get_timeline(chatroom_id=room_id)

        # 添加消息
        msg_type = json_info['msg_type']

        # type = {text, image, file, video, audio, combine, reply, invite}
        if msg_type == 'text' or msg_type == 'reply':

            msg_body = json_info['msg_body']
            msg_time = await sync_to_async(time.strftime)('%Y-%m-%d %H:%M:%S', time.localtime())

            if msg_type == 'reply':
                reply_id = json_info['reply_id']
                message = await database_sync_to_async(
                    create_message)(type=msg_type, body=msg_body, time=msg_time, sender=user_name, reply_id=reply_id)
                # Msg R3 for online cas
                await self.channel_layer.group_send(
                    self.chat_group_name, {
                        "type": "message_diffuse",
                        'msg_id': message.msg_id,
                        'msg_type': msg_type,
                        'msg_body': msg_body,
                        'reply_id': reply_id
                    }
                )

            else:
                message = await database_sync_to_async(
                    create_message)(type=msg_type, body=msg_body, time=msg_time, sender=user_name)
                # Msg R3 for online case
                await self.channel_layer.group_send(
                    self.chat_group_name, {
                        "type": "message_diffuse",
                        'msg_id': message.msg_id,
                        'msg_type': msg_type,
                        'msg_body': msg_body,
                    }
                )

            await sync_to_async(timeline.msg_line.append)(message.msg_id)

            # Ack 2
            await self.send(
                text_data=json.dumps({
                        "type": "Ack 2",
                        'msg_id': message.msg_id,
                    }
                )
            )


        elif msg_type == 'combine':
            # Fix
            msg_body = json_info['msg_body']
            msg_time = await sync_to_async(time.strftime)('%Y-%m-%d %H:%M:%S', time.localtime())

            message = await database_sync_to_async(
                create_message)(type=msg_type, body=msg_body, time=msg_time, sender=user_name)

            # Msg R3 for online case
            await self.channel_layer.group_send(
                self.chat_group_name, {
                    "type": "message_diffuse",
                    'msg_id': message.msg_id,
                    'msg_type': msg_type,
                    'msg_body': msg_body,
                }
            )

            await sync_to_async(timeline.msg_line.append)(message.msg_id)

            # Ack 2
            await self.send(
                text_data=json.dumps({
                        "type": "Ack 2",
                        'msg_id': message.msg_id,
                    }
                )
            )

        elif msg_type == 'invite':
            # Fix
            msg_body = json_info['msg_body']
            msg_time = await sync_to_async(time.strftime)('%Y-%m-%d %H:%M:%S', time.localtime())

            message = await database_sync_to_async(
                create_message)(type=msg_type, body=msg_body, time=msg_time, sender=user_name)
            # Msg R3 for online case
            await self.channel_layer.group_send(
                self.chat_group_name, {
                    "type": "message_diffuse",
                    'msg_id': message.msg_id,
                    'msg_type': msg_type,
                    'msg_body': msg_body,
                }
            )

            await sync_to_async(timeline.msg_line.append)(message.msg_id)

            # Ack 2
            await self.send(
                text_data=json.dumps({
                        "type": "Ack 2",
                        'msg_id': message.msg_id,
                    }
                )
            )

        elif msg_type == 'image' or msg_type == 'video' or msg_type == 'audio' or msg_type == 'file':
            pass

    async def acknowledge_message(self, json_info):
        '''
        json_info = {
            'is_back': False,
            'count': 1,
            # 'msg_id': 35
        }
        ''
        json_info = {
            'is_back': True,
            'count': 5,
            # 'msg_id': [16, 77, 33, 63, 12]
        }
        '''

        # Pipeline
        # called by Ack 4
        # send Ack 5 to cli B
        # move the cursor of cli B

        # 初始化
        user_name = self.cur_user
        is_back = json_info['is_back']
        count = json_info['count']

        if is_back:
            # 获取onliner，群聊和Timeline
            onliner = await filter_first_onlineuser(user_name)
            if onliner is None:
                await self.send('you are not in the chatroom')
                await self.close()

            room_id = onliner.chatroom_id
            chatroom = await filter_first_chatroom(chatroom_id=room_id)
            if chatroom is None:
                await self.send('chatroom not exists')
                await self.close()

            timeline = await filter_first_timeline(chatroom_id=room_id)

            # 移动Timeline的cursor
            lis = chatroom.mem_list.index(user_name)

            timeline.cursor_list[lis] += count

        else:
            # 获取onliner，群聊和Timeline
            onliner = await filter_first_onlineuser(user_name)
            if onliner is None:
                await self.send('you are not in the chatroom')
                await self.close()

            room_id = onliner.chatroom_id
            chatroom = await filter_first_chatroom(chatroom_id=room_id)
            if chatroom is None:
                await self.send('chatroom not exists')
                await self.close()

            timeline = await filter_first_timeline(chatroom_id=room_id)

            # 移动Timeline的cursor
            lis = chatroom.mem_list.index(user_name)

            timeline.cursor_list[lis] += 1

    async def find_chatroom(self, function_name, chatroom_id):
        chatroom_list_tem = await sync_to_async(ChatRoom.objects.filter)(chatroom_id=chatroom_id)
        chatroom = await sync_to_async(chatroom_list_tem.first)()

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
        user_id = await get_user_id(username)
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
        json_info = {
            'member_list': ['A', 'B'],
            'room_name': 'lob',
        }
        """
        username = await self.get_cur_username()
        room_name = json_info['room_name']
        member_list = json_info['member_list']

        chat_room = await create_chatroom(room_name, member_list, username)
        await sync_to_async(chat_room.save)()

        await self.send(text_data=json.dumps({
            'function': 'create_group',
            'chatroom_id': chat_room.chatroom_id
        }))

    async def delete_group(self, json_info):
        """
        json_info = {
            'chatroom_id': 114514,
        }
        """
        function_name = 'delete_group'

        chatroom_id = json_info['chatroom_id']
        chatroom = await self.find_chatroom(function_name, chatroom_id)

        if not chatroom is None:
            username = await self.get_cur_username()

            if await self.check_chatroom_master(function_name, chatroom, username):
                chat_timeline = await get_timeline(timeline_id=chatroom.timeline_id)
                chatroom.delete()
                chat_timeline.delete()

                await self.send(text_data=json.dumps({
                    'function': function_name,
                    'message': 'Success'
                }))

    async def appoint_manager(self, json_info):
        """
        json_info = {
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
        """
        json_info = {
            'chatroom_id': 114514,
            'new_master_name': 'ashitemaru'
        }
        """
        function_name = 'transfer_master'

        chatroom_id = json_info['chatroom_id']
        chatroom = await self.find_chatroom(function_name, chatroom_id)

        if chatroom is not None:
            username = await self.get_cur_username()

            if await self.check_chatroom_master(function_name, chatroom, username):
                new_master_name = json_info['new_master_name']

                new_master = await self.check_user_exist(function_name, new_master_name)
                if new_master is not None and \
                        await self.check_user_in_chatroom(function_name, chatroom, new_master_name):
                    chatroom.master_name = new_master_name
                    await self.send(text_data=json.dumps({
                        'function': function_name,
                        'message': 'Success'
                    }))

    async def add_group(self, json_info):
        pass

    async def leave_group(self, json_info):
        pass

    async def allow_add_group(self, json_info):
        pass

    async def release_notice(self, json_info):
        '''
        json_info = {
            'msg_type': 'text',
            'msg_body': 'hello',
        }
        '''

        msg_body = json_info['msg_body']


    async def remove_group_member(self, json_info):
        """
        json_info = {
            'chatroom_id': 114514,
            'member_name': 'ashitemaru'
        }
        """
        function_name = 'remove_group_member'

        chatroom_id = json_info['chatroom_id']
        chatroom = await self.find_chatroom(function_name, chatroom_id)

        if chatroom is not None:
            username = await self.get_cur_username()
            member_name = json_info['member_name']

            user = await self.check_user_exist(function_name, username)
            member = await self.check_user_exist(function_name, member_name, message='Member not found')

            if user is not None and member is not None and \
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

    async def withdraw_message(self, json_info):
        '''
        json_info = {
            msg_id: 114514
        }
        '''
        username = await self.get_cur_username()
        online_user = await filter_first_onlineuser(username)
        chatroom_id = online_user.chatroom_id
        chatroom = filter_first_chatroom(chatroom_id=chatroom_id)
        timeline = filter_first_timeline(chatroom_id=chatroom_id)
        # Fix


    async def fetch_friend_list(self, json_info):
        '''
        json_info = {

        }
        '''
        attribute_name = 'friendlist'

        username = json_info["username"]

        flist = await get_friendlist(username)

        return_list = []
        flist_len = len(flist.group_list)

        for i in range(flist_len):
            return_list.append({
                "groupname": flist.group_list[i],
                "username": []
            })
            for friend_name in flist.friend_list:
                friend = await filter_first_friend(username,friend_name)
                if friend is not None and flist.group_list[i] == friend.group_name:
                    return_list[i]['username'].append(friend_name)

        await self.send(text_data=json.dumps({
            'function': attribute_name,
            attribute_name: return_list,
        }))

    async def fetch_room(self, json_info):
        '''
        json_info = {

        }
        '''
        username = json_info['username']
        return_field = []
        async for room in ChatRoom.objects.all():
            for li, user in enumerate(room.mem_list):
                if user == username:
                    roomname = room.room_name
                    if room.is_private:
                        if room.mem_list[0] == username:
                            roomname = room.mem_list[1]
                        else:
                            roomname = room.mem_list[0]
                    return_field.append({
                        "roomid": room.chatroom_id,
                        "roomname": roomname,
                        "is_notice": room.is_notice[li],
                        "is_top": room.is_top[li]
                        #"is_private": room.is_private
                    })
                    break
        await self.send(text_data=json.dumps({
            "function": "fetchroom",
            "roomlist": return_field
        }))

    async def fetch_roominfo(self, json_info):
        chatroom_id = json_info['roomid']
        mem_list = []
        manager_list = []
        notice_list = []
        rooms = await sync_to_async(ChatRoom.objects.filter)(chatroom_id=chatroom_id)
        room = await sync_to_async(rooms.first)()
        for user in room.mem_list:
            mem_list.append(user)
        for manager in room.manager:
            manager_list.append(manager)
        for notice in room.notice_list:
            notice_list.append(notice)
        master = room.master_name
        mem_count = room.mem_count
        await self.send(text_data=json.dumps({
            "function": "fetchroominfo",
            "mem_list": mem_list,
            "manager_list": manager_list,
            "master": master,
            "mem_count": mem_count,
            "notice_list": notice_list
        }))


    async def fetch_message(self, json_info):
        '''
        json_info = {


        }
        '''
        chatroom_id = json_info['chatroom_id']
        username = json_info['username']
        room1 = await sync_to_async(ChatRoom.objects.filter)(chatroom_id=chatroom_id)
        room = await sync_to_async(room1.first)()
        return_field = []
        for li, user in enumerate(room.mem_list):
            if user == username:
                await sync_to_async(room.save)()
                break

        timeline = await get_timeline(chatroom_id=room.chatroom_id)
        for msg in timeline.msg_line:
            cur_message1 = await sync_to_async(Message.objects.filter)(msg_id=msg)
            cur_message = await sync_to_async(cur_message1.first)()
            return_field.append({
                "body": cur_message.body,
                "id": cur_message.msg_id,
                "time": cur_message.time,
                "sender": cur_message.sender
            })

        await self.send(text_data=json.dumps({
            "function": "fetchmessage",
            "messagelist": return_field
        }))

    async def add_group_member(self, json_info):
        pass
