from channels.exceptions import StopConsumer
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model, authenticate

import json
from datetime import datetime
import time

from UserManage.models import *
from Chat.models import *
from FriendRelation.models import *
from UserManage.models import *
from utils.utils_cryptogram import async_decode
from utils.utils_database import *
import os

CONSUMER_OBJECT_LIST = []


async def modify_add_request_list_with_username(other_username, add_list, answer, mode=0):
    """
    mode = 0 : add_list.reply
    mode = 1 : add_list.apply
    """
    index = await search_ensure_false_request_index(other_username, add_list, mode=mode)
    if index == -1:
        return False
    if mode == 0:
        add_list.reply_answer[index] = answer
        add_list.reply_ensure[index] = True
    elif mode == 1:
        add_list.apply_answer[index] = answer
        add_list.apply_ensure[index] = True
    await sync_to_async(add_list.save)()
    return True


async def manager_fetch_invite_list(chatroom):
    l = chatroom.manager_list.copy()
    l.append(chatroom.master_name)

    for username in l:
        for index, onliner in enumerate(CONSUMER_OBJECT_LIST):
            if username == onliner.cur_user:
                CONSUMER_OBJECT_LIST[index].fetch_invite_list({"username": username})


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
    if username == chatroom.master_name:
        return 2
    elif username in chatroom.manager_list:
        return 1
    else:
        return 0


async def chatroom_delete_member(chatroom, member_name):
    timeline = await get_timeline(chatroom.timeline_id)

    for index, username in enumerate(chatroom.mem_list):
        if username == member_name:
            chatroom.mem_list.pop(index)
            chatroom.is_top.pop(index)
            chatroom.is_notice.pop(index)
            chatroom.is_specific.pop(index)
            timeline.cursor_list.pop(index)

            if username in chatroom.manager_list:
                chatroom.manager_list.remove(username)

            for message_id in timeline.msg_line:
                message = await get_message(message_id)
                message.read_list.pop(index)
                message.delete_list.pop(index)
                await database_sync_to_async(message.save)()

            chatroom.mem_count -= 1
            break
    await database_sync_to_async(chatroom.save)()
    await database_sync_to_async(timeline.save)()


async def chatroom_add_member(chatroom, member_name):
    timeline = await get_timeline(chatroom.timeline_id)

    chatroom.mem_list.append(member_name)
    chatroom.is_top.append(False)
    chatroom.is_notice.append(True)
    chatroom.is_specific.append(False)
    chatroom.mem_count += 1

    timeline.cursor_list.append(0)

    for message_id in timeline.msg_line:
        message = await get_message(message_id)
        message.read_list.append(False)
        message.delete_list.append(False)
        await database_sync_to_async(message.save)()

    await database_sync_to_async(chatroom.save)()
    await database_sync_to_async(timeline.save)()


class UserConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.room_id = None
        self.room_name = None
        self.chatroom_name = None
        self.cur_user = None
        self.count = 0

    async def get_cur_username(self):
        return self.cur_user

    async def connect(self):
        await self.accept()

    async def disconnect(self, code):
        username = self.cur_user
        async for chatroom in ChatRoom.objects.all():
            if username in chatroom.mem_list:
                timeline = await get_timeline(chatroom_id=chatroom.chatroom_id)
                lis = await sync_to_async(chatroom.mem_list.index)(username)
                timeline.cursor_list[lis] = 0
                await sync_to_async(timeline.save)()
                await self.channel_layer.group_discard("chat_" + str(chatroom.chatroom_id), self.channel_name)

        user = await filter_first_user(username)
        if user is not None:
            im_user = await database_sync_to_async(IMUser.objects.get)(user=user)
            im_user.is_login = False
            await sync_to_async(im_user.save)()

        CONSUMER_OBJECT_LIST.remove(self)
        raise StopConsumer()

    async def receive(self, text_data=None, bytes_data=None):

        json_info = json.loads(text_data)
        function = json_info["function"]

        # Friend Function
        if function == 'heartbeat':
            await self.heart_beat()

        elif function == 'apply':
            await self.apply_friend(json_info)

        elif function == 'confirm':
            await self.confirm_friend(json_info)

        elif function == 'decline':
            await self.decline_friend(json_info)

        elif function == 'refresh':
            await self.refresh(json_info)

        elif function == 'fetchapplylist':
            await self.fetch_apply_list(json_info)

        elif function == 'fetchreceivelist':
            await self.fetch_reply_list(json_info)

        elif function == 'fetchfriendlist':
            await self.fetch_friend_list(json_info)

        # Chat Function
        # 初始化所有私聊/群聊
        elif function == 'add_channel':
            await self.add_channel(json_info)

        # 连接某个私聊/群聊
        elif function == 'add_chat':
            await self.add_chat(json_info)

        # 离开某个私聊/群聊
        elif function == 'leave_chat':
            await self.leave_chat(json_info)

        # 发送各种消息
        # {text}: 直接处理
        # {rel}: 添加
        # {combine}: 转发
        # {image, audio, file}: 采用下载链接处理
        elif function == 'send_message':
            await self.send_message(json_info)

        # 撤回消息
        elif function == 'withdraw_message':
            await self.withdraw_message(json_info)

        # 创建群聊
        elif function == 'create_group':
            await self.create_group(json_info)

        # 群主删除群聊
        elif function == 'delete_chat_group':
            await self.delete_chat_group(json_info)

        # 用户自己申请加入群聊
        # elif function == 'apply_add_group':
        #    await self.apply_add_group(json_info)

        # 群主/管理员处理申请用户加入群聊信息
        elif function == 'reply_add_group':
            await self.reply_add_group(json_info)

        # 用户自己退出群聊
        elif function == 'leave_group':
            await self.leave_group(json_info)

        # 群主任命管理员
        elif function == 'appoint_manager':
            await self.appoint_manager(json_info)

        # 群主卸任管理员
        elif function == 'remove_manager':
            await self.remove_manager(json_info)

        # 群主转让给他人
        elif function == 'transfer_master':
            await self.transfer_master(json_info)

        # 群主/管理员直接添加用户到群聊
        elif function == 'add_group_member':
            await self.add_group_member(json_info)

        # 群主/管理员直接移除群成员
        elif function == 'remove_group_member':
            await self.remove_group_member(json_info)

        # 获取用户的所有私聊/群聊信息
        elif function == "fetch_room":
            await self.fetch_room(json_info)

        # 获取用户作为群主/管理对应群的入群申请
        elif function == "fetch_invite_list":
            await self.fetch_invite_list(json_info)

        # 获取某一个私聊/群聊的具体信息
        elif function == "fetch_roominfo":
            await self.fetch_roominfo(json_info)

        # 修改私聊/群聊免打扰属性
        elif function == "revise_is_notice":
            await self.revise_is_notice(json_info)

        # 修改私聊/群聊置顶属性
        elif function == "revise_is_top":
            await self.revise_is_top(json_info)

        # 修改特殊私聊/群聊属性
        elif function == 'revise_is_specific':
            await self.revise_is_specific(json_info)

        # 设置已读消息
        elif function == 'read_message':
            await self.read_message(json_info)

        # 删除消息
        elif function == 'delete_message':
            await self.delete_message(json_info)

        # 二次检验密码
        elif function == 'examine_password_twice':
            await self.examine_password_twice(json_info)

    async def heart_beat(self):
        """
        json_info = {}
        """
        await self.send(text_data=json.dumps({
            'function': 'heartbeatconfirm',
        }))

    async def apply_friend(self, json_info):
        """
        json_info = {
            'username': 'zj',
            'to': 'zj',
            'from': 'zj2'
        }
        """
        function_name = "apply_friend"

        username = json_info['username']
        apply_from = json_info['from']
        apply_to = json_info['to']
        applyer_add_list = await filter_first_addlist(apply_from)
        receiver_add_list = await filter_first_addlist(apply_to)

        # 确保被回复前不能重复发送
        # mode=1意为在applyer_add_list.applylist中寻找apply_to
        if not await search_ensure_false_request_index(apply_to, applyer_add_list, mode=1) == -1:
            await self.send(text_data=json.dumps({
                'function': function_name,
                'message': "List Has Been Sent"
            }))

        elif apply_to in (await sync_to_async(FriendList.objects.get)(user_name=apply_from)).friend_list:
            await self.send(text_data=json.dumps({
                'function': function_name,
                'message': "Is Already a Friend"
            }))

        else:
            applyer_add_list.apply_list.append(apply_to)
            applyer_add_list.apply_answer.append(False)
            applyer_add_list.apply_ensure.append(False)
            await sync_to_async(applyer_add_list.save)()

            receiver_add_list.reply_list.append(apply_from)
            receiver_add_list.reply_answer.append(False)
            receiver_add_list.reply_ensure.append(False)
            await sync_to_async(receiver_add_list.save)()

            # 若receiver在线则申请发送到receiver
            from_add_list = await get_addlist(apply_from)
            to_add_list = await get_addlist(apply_to)
            from_return_field = list()
            to_return_field = list()
            from_len = len(from_add_list.apply_list)
            to_len = len(to_add_list.reply_list)

            for li in range(from_len):
                from_return_field.append({
                    "username": from_add_list.apply_list[li],
                    "is_confirmed": from_add_list.apply_answer[li],
                    "make_sure": from_add_list.apply_ensure[li]
                })

            for li in range(to_len):
                to_return_field.append({
                    "username": to_add_list.reply_list[li],
                    "is_confirmed": to_add_list.reply_answer[li],
                    "make_sure": to_add_list.reply_ensure[li]
                })

            for index, user in enumerate(CONSUMER_OBJECT_LIST):
                if user.cur_user == apply_from:
                    await CONSUMER_OBJECT_LIST[index].send(text_data=json.dumps({
                        'function': 'applylist',
                        'applylist': from_return_field
                    }))

                elif user.cur_user == apply_to:
                    await CONSUMER_OBJECT_LIST[index].send(text_data=json.dumps({
                        'function': 'receivelist',
                        'receivelist': to_return_field
                    }))

    async def confirm_friend(self, json_info):
        username = json_info['username']
        apply_from = json_info['from']
        apply_to = json_info['to']
        receiver_add_list = await get_addlist(apply_to)
        applyer_add_list = await get_addlist(apply_from)

        # 修改数据库
        await modify_add_request_list_with_username(apply_from, receiver_add_list, True)
        await modify_add_request_list_with_username(apply_to, applyer_add_list, True, mode=1)

        friend_list1 = await get_friendlist(username)
        friend_list1.friend_list.append(apply_from)
        await sync_to_async(friend_list1.save)()

        friend_list2 = await get_friendlist(apply_from)
        friend_list2.friend_list.append(username)
        await sync_to_async(friend_list2.save)()

        friend1 = Friend(user_name=username, friend_name=apply_from, group_name=friend_list1.group_list[0])
        friend2 = Friend(user_name=apply_from, friend_name=username, group_name=friend_list2.group_list[0])

        await sync_to_async(friend1.save)()
        await sync_to_async(friend2.save)()

        chatroom = await create_chatroom('private_chat', [username, apply_from], username, is_private=True)

        # 若applyer在线结果发送到applyer
        return_field = {
            "function": "confirm"
        }

        await self.send(text_data=json.dumps(return_field))

        await self.fetch_friend_list({"username": username})
        await self.fetch_reply_list({"username": username})

        await self.channel_layer.group_add("chat_" + str(chatroom.chatroom_id), self.channel_name)

        for index, user in enumerate(CONSUMER_OBJECT_LIST):
            if user.cur_user == apply_from:
                await CONSUMER_OBJECT_LIST[index].channel_layer.group_add("chat_" + str(chatroom.chatroom_id),
                                                                          user.channel_name)
                await CONSUMER_OBJECT_LIST[index].fetch_friend_list({"username": user.cur_user})
                await CONSUMER_OBJECT_LIST[index].fetch_apply_list({"username": user.cur_user})
                await CONSUMER_OBJECT_LIST[index].fetch_room({"username": user.cur_user})

    async def decline_friend(self, json_info):
        # 修改数据库
        apply_from = json_info['from']
        apply_to = json_info['to']
        receiver_add_list = await get_addlist(apply_to)
        applyer_add_list = await get_addlist(apply_from)

        await modify_add_request_list_with_username(apply_from, receiver_add_list, False)
        await modify_add_request_list_with_username(apply_to, applyer_add_list, False, mode=1)

        return_field = {
            "function": "decline"
        }
        await self.send(text_data=json.dumps(return_field))
        username = await self.get_cur_username()
        await self.fetch_reply_list({
            "username": username
        })

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

    async def add_channel(self, json_info):
        """
        json_info = {
            'username': 'default',
        }
        """
        username = json_info['username']
        self.cur_user = username
        CONSUMER_OBJECT_LIST.append(self)
        async for chatroom in ChatRoom.objects.all():
            if username in chatroom.mem_list:
                await self.channel_layer.group_add("chat_" + str(chatroom.chatroom_id), self.channel_name)

    async def add_chat(self, json_info):
        """
        json_info = {
            'room_id': 5,
            'room_name': 'default',
        }
        """
        room_name = json_info['room_name']
        room_id = json_info['room_id']

        self.room_id = room_id
        self.room_name = room_name
        self.chatroom_name = "chat_" + str(room_id)

    async def leave_chat(self, json_info):
        """
        json_info = {}
        """
        self.room_id = None
        self.room_name = None
        self.chatroom_name = None

    async def group_send(self, chatroom_name, return_field):
        await self.channel_layer.group_send(chatroom_name, return_field)

    async def message_diffuse(self, event):
        msg_id = event["msg_id"]
        msg_body = event["msg_body"]
        msg_time = event['msg_time']
        msg_type = event['msg_type']
        sender = event['sender']
        room_id = event['room_id']
        read_list = event['read_list']
        delete_list = event['delete_list']

        if msg_type == 'reply':
            reply_id = event['reply_id']
        else:
            reply_id = -1

        if msg_type == 'combine':
            combine_list = event['combine_list']
        else:
            combine_list = list()

        users = await sync_to_async(User.objects.filter)(username=sender)
        user = await sync_to_async(users.first)()
        imusers = await sync_to_async(IMUser.objects.filter)(user=user)
        imuser = await sync_to_async(imusers.first)()
        avatar = os.path.join("/static/media/", str(imuser.avatar))
        if avatar == "/static/media/":
            avatar += "pic/default.jpeg"

        return_field = {
            'function': 'Msg',
            'msg_id': msg_id,
            "msg_body": msg_body,
            'msg_time': msg_time,
            'msg_type': msg_type,
            'sender': sender,
            'reply_id': reply_id,
            'combine_list': combine_list,
            'room_id': room_id,
            'avatar': avatar,
            'read_list': read_list,
            'delete_list': delete_list,
            'is_delete': False
        }

        await self.send(text_data=json.dumps(return_field))

    async def withdraw_diffuse(self, event):
        room_id = event["room_id"]
        msg_id = event["msg_id"]

        return_field = {
            'function': 'withdraw_message',
            'msg_id': msg_id,
            'room_id': room_id
        }

        await self.send(text_data=json.dumps(return_field))

    async def read_diffuse(self, event):
        read_message_list = event['read_message_list']
        chatroom_id = event['chatroom_id']
        read_user = event['read_user']
        return_field = {
            'function': 'read_message',
            'read_user': read_user,
            'chatroom_id': chatroom_id,
            'read_message_list': read_message_list
        }
        await self.send(text_data=json.dumps(return_field))

    async def send_message(self, json_info):
        """
        text: json_info = {
            'msg_type': 'text',
            'msg_body': 'hello',
        }

        reply: json_info = {
            'msg_type': 'reply',
            'msg_body': 'hello',
            'reply_id': 16,
        }

        combine: json_info = {
            'msg_type': 'combine',
            'combine_list': [16, 17],
            'transroom_id': 36,
        }
        """

        # Pipeline
        # called by Msg R1
        # send Msg R3 to cli Bs
        # send Ack 2 to cli A
        # move the cursor of cli A

        # 初始化
        username = self.cur_user
        room_id = self.room_id
        room_name = self.room_name
        chatroom_name = self.chatroom_name

        # 添加消息
        msg_type = json_info['msg_type']
        msg_body = json_info['msg_body']
        msg_time = await sync_to_async(time.strftime)('%Y-%m-%d %H:%M:%S', time.localtime())
        message = await create_message(type=msg_type, body=msg_body, time=msg_time, sender=username)
        msg_id = message.msg_id
        users = await sync_to_async(User.objects.filter)(username=username)
        user = await sync_to_async(users.first)()
        imusers = await sync_to_async(IMUser.objects.filter)(user=user)
        imuser = await sync_to_async(imusers.first)()

        if msg_type == 'combine':
            transroom_id = json_info['transroom_id']
            chatroom = await filter_first_chatroom(chatroom_id=transroom_id)
            timeline = await get_timeline(chatroom_id=transroom_id)
        else:
            chatroom = await filter_first_chatroom(chatroom_id=room_id)
            timeline = await get_timeline(chatroom_id=room_id)

        # Move Here
        # 修改数据库
        lis = await sync_to_async(chatroom.mem_list.index)(username)
        timeline.cursor_list[lis] += 1
        await sync_to_async(timeline.msg_line.append)(msg_id)
        await sync_to_async(timeline.save)()

        message.read_list = list()
        message.delete_list = list()
        for member_name in chatroom.mem_list:
            message.delete_list.append(False)
            if member_name == username:
                message.read_list.append(True)
            else:
                message.read_list.append(False)
        await sync_to_async(message.save)()
        read_list = message.read_list
        delete_list = message.delete_list

        avatar = os.path.join("/static/media/", str(imuser.avatar))
        if avatar == "/static/media/":
            avatar += "pic/default.jpeg"

        Msg_field = {
            "type": "message_diffuse",
            'msg_id': msg_id,
            'msg_type': msg_type,
            'msg_body': msg_body,
            'msg_time': msg_time,
            'sender': username,
            'room_id': room_id if msg_type != 'combine' else transroom_id,
            'avatar': avatar,
            'read_list': read_list,
            'delete_list': delete_list,
        }

        Ack_field = {
            "function": "Ack2",
            'msg_id': msg_id,
        }

        if msg_type == 'text' or msg_type == 'notice':
            # Msg R3 for online case
            await self.group_send(chatroom_name, Msg_field)

            # Ack 2
            await self.send(text_data=json.dumps(Ack_field))

        elif msg_type == 'reply':
            reply_id = json_info['reply_id']
            Msg_field['reply_id'] = reply_id
            message.reply_id = reply_id
            await sync_to_async(message.save)()

            replied_message = await filter_first_message(msg_id=reply_id)
            replied_message.reply_count += 1
            await sync_to_async(replied_message.save)()

            # Msg R3 for online case
            await self.group_send(chatroom_name, Msg_field)

            # Ack 2
            await self.send(text_data=json.dumps(Ack_field))

        elif msg_type == 'combine':
            combine_list = json_info['combine_list']
            Msg_field['combine_list'] = combine_list
            message.combine_list = combine_list
            await sync_to_async(message.save)()

            # Msg R3 for online case
            await self.group_send(chatroom_name, Msg_field)

            # Ack 2
            await self.send(text_data=json.dumps(Ack_field))

        elif msg_type == 'invite':
            function_name = 'send_message_invite'
            if chatroom is not None:
                invited_name = msg_body
                invited_user = await self.check_user_exist(function_name, invited_name)
                if invited_user is not None:
                    if invited_name in chatroom.mem_list:
                        await self.send(text_data=json.dumps({
                            'function': function_name,
                            'message': 'User is already in the group'
                        }))
                    else:
                        username = await self.get_cur_username()
                        # Fix: Dumplication
                        # message = await database_sync_to_async(create_message)(type='invite', body=invited_name,
                        #                                                       time=msg_time, sender=username)

                        # Msg R3 for online case
                        await self.group_send(chatroom_name, Msg_field)

                        # Ack 2
                        await self.send(text_data=json.dumps(Ack_field))

                        # 群主/管理员权限直接拉进群
                        if await get_power(chatroom, username) != 0:
                            message.answer = 1
                            await sync_to_async(message.save)()
                            await chatroom_add_member(chatroom, invited_name)

                        invite_list = await get_invite_list(chatroom_id=chatroom.chatroom_id)
                        invite_list.msg_list.append(message.msg_id)
                        await database_sync_to_async(invite_list.save)()

                        await self.send(text_data=json.dumps({
                            'function': function_name,
                            'message': 'Invite Member Success',
                            'message_id': message.msg_id
                        }))

                        await manager_fetch_invite_list(chatroom)

        elif msg_type == 'image' or msg_type == 'video' or msg_type == 'audio' or msg_type == 'file':
            pass

    async def acknowledge_message(self, json_info):
        """
        json_info = {
            'is_back': False,
            'count': 1,
            'room_id': 6,
        }
        """

        # Pipeline
        # called by Ack 4
        # move the cursor of cli B

        # 初始化
        username = self.cur_user
        room_id = json_info['room_id']
        is_back = json_info['is_back']
        count = json_info['count']

        chatroom = await filter_first_chatroom(chatroom_id=room_id)
        timeline = await filter_first_timeline(chatroom_id=room_id)

        # 移动Timeline的cursor
        lis = chatroom.mem_list.index(username)

        if is_back:
            timeline.cursor_list[lis] += count
        else:
            timeline.cursor_list[lis] += 1

    async def withdraw_message(self, json_info):
        """
        json_info = {
            'msg_id': 114514,
        }
        """
        # 初始化
        msg_id = json_info['msg_id']

        room_id = self.room_id
        room_name = self.room_name
        chatroom_name = self.chatroom_name

        # 判断是否超时
        message = await filter_first_message(msg_id=msg_id)
        msg_time = message.time
        now_time = await sync_to_async(time.strftime)('%Y-%m-%d %H:%M:%S', time.localtime())

        msg_datetime = datetime.strptime(msg_time, "%Y-%m-%d %H:%M:%S")
        now_datetime = datetime.strptime(now_time, "%Y-%m-%d %H:%M:%S")

        delta = now_datetime - msg_datetime
        delta_days = delta.days
        delta_hours = delta.seconds // 3600
        delta_minutes = (delta.seconds % 3600) // 60

        if delta_days != 0 or delta_hours != 0 or delta_minutes > 5:
            await self.send(text_data=json.dumps({
                'function': 'withdraw_overtime',
                'msg_id': msg_id,
            }))
            return

        chatroom = await filter_first_chatroom(chatroom_id=room_id)
        timeline = await get_timeline(chatroom_id=room_id)

        lis = await sync_to_async(timeline.msg_line.index)(msg_id)

        await sync_to_async(timeline.msg_line.pop)(lis)
        await sync_to_async(timeline.save)()

        # 移动用户的cursor
        for i in range(len(timeline.cursor_list)):
            timeline.cursor_list[i] -= 1

        # 发送给在线用户
        Withdraw_field = {
            'type': 'withdraw_diffuse',
            'msg_id': msg_id,
            'room_id': room_id,
        }
        await self.group_send(chatroom_name, Withdraw_field)

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
        manager_user = await get_user(username)
        if manager_user is None:
            await self.send(text_data=json.dumps({
                'function': function_name,
                'message': message
            }))
        return manager_user

    async def check_user_in_chatroom(self, function_name, chatroom, username, message='User is not in the group'):
        if username in chatroom.mem_list:
            return True
        else:
            await self.send(text_data=json.dumps({
                'function': function_name,
                'message': message
            }))
            return False

    async def message_pre_treat(self, function_name, message_type, answer):
        if message_type != 'invite':
            await self.send(text_data=json.dumps({
                'function': function_name,
                'message': 'Message Type Error'
            }))
            return False
        elif answer != -1:
            await self.send(text_data=json.dumps({
                'function': function_name,
                'message': 'Message Already Replied'
            }))
            return False
        else:
            return True

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

        chatroom = await create_chatroom(room_name, member_list, username)

        chatroom_name = 'chat_' + str(chatroom.chatroom_id)
        for membername in chatroom.mem_list:
            for li, onliner in enumerate(CONSUMER_OBJECT_LIST):
                if onliner.cur_user == membername:
                    await CONSUMER_OBJECT_LIST[li].channel_layer.group_add(chatroom_name, onliner.channel_name)
                    await CONSUMER_OBJECT_LIST[li].fetch_room({
                        'username': onliner.cur_user
                    })
                    break

    async def delete_chat_group(self, json_info):
        """
        json_info = {
            'chatroom_id': 114514,
        }
        """
        function_name = 'delete_chat_group'

        chatroom_id = json_info['chatroom_id']
        chatroom = await self.find_chatroom(function_name, chatroom_id)

        if chatroom is not None and not chatroom.is_private:
            username = await self.get_cur_username()

            if await self.check_chatroom_master(function_name, chatroom, username):
                mem_list = chatroom.mem_list.copy()

                chat_timeline = await get_timeline(timeline_id=chatroom.timeline_id)

                invite_list = await get_invite_list(chatroom_id=chatroom_id)
                await sync_to_async(chatroom.delete)()
                await sync_to_async(chat_timeline.delete)()
                await sync_to_async(invite_list.delete)()

                await self.send(text_data=json.dumps({
                    'function': 'delete_chat_group',
                    'message': 'Delete Group Success'
                }))

                for i in mem_list:
                    for index, user in enumerate(CONSUMER_OBJECT_LIST):
                        if user.cur_user == i:
                            await CONSUMER_OBJECT_LIST[index].fetch_room({'username': user.cur_user})

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

        if chatroom is not None and not chatroom.is_private:
            username = await self.get_cur_username()
            manager_name = json_info['manager_name']

            if await self.check_chatroom_master(function_name, chatroom, username):
                manager_user = await self.check_user_exist(function_name, manager_name)

                if manager_user is not None and \
                        await self.check_user_in_chatroom(function_name, chatroom, manager_name):
                    if manager_name in chatroom.manager_list:
                        await self.send(text_data=json.dumps({
                            'function': 'appoint_manager',
                            'message': 'User is already an manager'
                        }))
                    else:
                        chatroom.manager_list.append(manager_name)
                        await sync_to_async(chatroom.save)()
                        await self.send(text_data=json.dumps({
                            'function': 'appoint_manager',
                            'message': 'Appoint Manager Success'
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

        if chatroom is not None and not chatroom.is_private:
            username = await self.get_cur_username()

            if await self.check_chatroom_master(function_name, chatroom, username):
                new_master_name = json_info['new_master_name']

                new_master = await self.check_user_exist(function_name, new_master_name)
                if new_master is not None and \
                        await self.check_user_in_chatroom(function_name, chatroom, new_master_name):
                    chatroom.master_name = new_master_name
                    await sync_to_async(chatroom.save)()
                    await self.send(text_data=json.dumps({
                        'function': 'transfer_master',
                        'message': 'Transfer Master Success'
                    }))

    # async def apply_add_group(self, json_info):
    #     """
    #     json_info = {
    #         'chatroom_id': 114514,
    #         ‘invited_name’: 'ashitemaru'
    #     }
    #     """
    #     function_name = 'apply_add_group'
    #
    #     chatroom_id = json_info['chatroom_id']
    #     invited_name = json_info['invited_name']
    #     chatroom = await self.find_chatroom(function_name, chatroom_id)
    #
    #     if chatroom is not None:
    #         invited_user = await self.check_user_exist(function_name, invited_name)
    #
    #         if invited_user is not None:
    #             if invited_name in chatroom.mem_list:
    #                 await self.send(text_data=json.dumps({
    #                     'function': function_name,
    #                     'message': 'User is already in the group'
    #                 }))
    #             else:
    #                 username = await self.get_cur_username()
    #                 user = await get_user(username)
    #
    #                 msg_time = await sync_to_async(time.strftime)('%Y-%m-%d %H:%M:%S', time.localtime())
    #                 message = await database_sync_to_async(create_message)(type='invite', body=invited_name,
    #                                                                        time=msg_time, sender=username)
    #
    #                 await sync_to_async(message.save)()
    #                 if get_power(chatroom, username) != 0:
    #                     message.answer = 1
    #                     await sync_to_async(message.save)()
    #                     await chatroom_add_member(chatroom, username)
    #
    #                 await self.send(text_data=json.dumps({
    #                     'function': function_name,
    #                     'message': 'Success',
    #                     'type': 'invite',
    #                     'answer': message.answer,
    #                     'body': invited_name,
    #                     'time': msg_time,
    #                     'sender': username
    #                 }))
    #
    #                 await manager_fetch_invite_list(chatroom)

    async def reply_add_group(self, json_info):
        """
        json_info = {
            'chatroom_id': 114514,
            'message_id': 114514,
            'answer' : -1: 未处理 1: 同意 0: 拒绝
        }
        """
        function_name = 'reply_add_group'

        chatroom_id = json_info['chatroom_id']
        message_id = json_info['message_id']

        message = await get_message(message_id)
        message_type = message.type
        answer = json_info['answer']
        invited_name = await async_decode(message.body)

        chatroom = await self.find_chatroom(function_name, chatroom_id)

        if chatroom is not None:

            print("reply add: " + str(message.answer) + " id: " + str(message.msg_id))

            if await self.message_pre_treat(function_name, message_type, message.answer):

                invited_user = await self.check_user_exist(function_name, invited_name)

                if invited_user is not None:
                    if invited_name in chatroom.mem_list:
                        await self.send(text_data=json.dumps({
                            'function': function_name,
                            'message': 'User is already in the group'
                        }))
                    else:
                        username = await self.get_cur_username()
                        user = await get_user(username)
                        if await get_power(chatroom, username) == 0:
                            await self.send(text_data=json.dumps({
                                'function': function_name,
                                'message': 'Permission denied'
                            }))
                        else:
                            message.answer = answer
                            await database_sync_to_async(message.save)()

                            if answer == 1:
                                await chatroom_add_member(chatroom, invited_name)

                            await self.send(text_data=json.dumps({
                                'function': function_name,
                                'message': 'Reply Add Group Success'
                            }))

    async def leave_group(self, json_info):
        """
        json_info = {
            'chatroom_id': 114514,
        }
        """
        function_name = 'leave_group'

        chatroom_id = json_info['chatroom_id']
        chatroom = await self.find_chatroom(function_name, chatroom_id)

        if chatroom is not None and not chatroom.is_private:
            username = await self.get_cur_username()
            user = await get_user(username)

            if await self.check_user_in_chatroom(function_name, chatroom, username):
                if username == chatroom.master_name:
                    await self.send(text_data=json.dumps({
                        'function': function_name,
                        'message': 'You are group master'
                    }))
                else:
                    tem = chatroom.mem_list.copy()

                    await chatroom_delete_member(chatroom, username)

                    await self.send(text_data=json.dumps({
                        'function': 'leave_group',
                        'message': 'Success',
                        'test_mem1': "pre" + ";".join(tem),
                        'test_mem2': "after" + ";".join(chatroom.mem_list),
                    }))

                    for i in chatroom.mem_list:
                        for index, username in enumerate(CONSUMER_OBJECT_LIST):
                            if i == username:
                                await CONSUMER_OBJECT_LIST[index].fetch_roominfo(json_info)
                                await CONSUMER_OBJECT_LIST[index].fetch_room(json_info)
                                break

    async def add_group_member(self, json_info):
        """
        json_info = {
            'chatroom_id': 114514,
            'added_username": "ashitemaru"
        }
        """
        pass

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

        if chatroom is not None and not chatroom.is_private:
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
                    await chatroom_delete_member(chatroom, member_name)
                    await sync_to_async(chatroom.save)()
                    await self.send(text_data=json.dumps({
                        'function': function_name,
                        'message': 'Remove Group Member Success'
                    }))

    async def read_message(self, json_info):
        """
        json_info = {
            'chatroom_id': 114514,
            'read_message_list': [13, 234, 123]
        }
        """
        username = self.cur_user
        chatroom_id = json_info['chatroom_id']
        read_message_list = json_info['read_message_list']
        chatroom_name = 'chat_' + str(chatroom_id)

        chatroom = await filter_first_chatroom(chatroom_id=chatroom_id)

        member_lis = chatroom.mem_list.index(username)

        for read_msg_id in read_message_list:
            message = await filter_first_message(msg_id=read_msg_id)
            message.read_list[member_lis] = True
            await sync_to_async(message.save)()

        Read_field = {
            'type': 'read_diffuse',
            'read_message_list': read_message_list,
            'read_user': username,
            'chatroom_id': chatroom_id,
        }
        await self.group_send(chatroom_name, Read_field)

    async def delete_message(self, json_info):
        """
        json_info = {
            'msg_id': 114514
        }
        """
        msg_id = json_info['msg_id']
        username = self.cur_user
        room_id = self.room_id

        chatroom = await filter_first_chatroom(chatroom_id=room_id)
        message = await filter_first_message(msg_id=msg_id)
        lis = await sync_to_async(chatroom.mem_list.index)(username)
        message.delete_list[lis] = True
        await sync_to_async(message.save)()

        await self.send(text_data=json.dumps({
            'function': 'delete_message',
            'msg_id': msg_id
        }))

    async def fetch_friend_list(self, json_info):
        """
        json_info = {

        }
        """
        username = await self.get_cur_username()
        flist = await get_friendlist(username)

        return_list = []
        flist_len = len(flist.group_list)

        for i in range(flist_len):
            return_list.append({
                "groupname": flist.group_list[i],
                "username": list()
            })
            for friend_name in flist.friend_list:
                friend = await filter_first_friend(username, friend_name)
                if friend is not None and flist.group_list[i] == friend.group_name:
                    return_list[i]['username'].append(friend_name)

        await self.send(text_data=json.dumps({
            'function': 'friendlist',
            'friendlist': return_list,
        }))

    async def fetch_room(self, json_info):
        """
        json_info = {
            'username': 'Alice'
        }
        """
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
                    chatroom_id = room.chatroom_id
                    room1 = await sync_to_async(ChatRoom.objects.filter)(chatroom_id=chatroom_id)
                    room = await sync_to_async(room1.first)()
                    message_list = list()

                    timeline = await get_timeline(chatroom_id=room.chatroom_id)
                    for msg in timeline.msg_line:
                        cur_message1 = await sync_to_async(Message.objects.filter)(msg_id=msg)
                        cur_message = await sync_to_async(cur_message1.first)()

                        if cur_message.type == 'invite':
                            if get_power(room, username)==0:
                                continue

                        users = await sync_to_async(User.objects.filter)(username=cur_message.sender)
                        user = await sync_to_async(users.first)()
                        if user is None:
                            avatar = "/static/media/pic/default.jpeg"
                        else:
                            imusers = await sync_to_async(IMUser.objects.filter)(user=user)
                            imuser = await sync_to_async(imusers.first)()
                            avatar = os.path.join("/static/media/", str(imuser.avatar))
                            if avatar == "/static/media/":
                                avatar += "pic/default.jpeg"

                        is_delete = cur_message.delete_list[li]

                        message_list.append({
                            "msg_body": await async_decode(cur_message.body),
                            "msg_id": cur_message.msg_id,
                            "msg_type": cur_message.type,
                            "msg_time": cur_message.time,
                            "sender": cur_message.sender,
                            "avatar": avatar,
                            "combine_list": cur_message.combine_list,
                            "read_list": cur_message.read_list,
                            "is_delete": is_delete,
                            # "reply_count": cur_message.reply_count
                        })
                    return_field.append({
                        "roomid": room.chatroom_id,
                        "roomname": roomname,
                        "is_notice": room.is_notice[li],
                        "is_top": room.is_top[li],
                        "message_list": message_list,
                        "is_private": room.is_private,
                        "is_specific": room.is_specific[li],
                        "index": li
                    })
                    break

        await self.send(text_data=json.dumps({
            "function": "fetchroom",
            "roomlist": return_field
        }))

        # await self.fetch_invite_list(json_info)

    async def fetch_roominfo(self, json_info):
        """
        json_info = {}
        """
        chatroom_id = json_info['roomid']
        mem_list = []
        manager_list = []
        notice_list = []
        rooms = await sync_to_async(ChatRoom.objects.filter)(chatroom_id=chatroom_id)
        room = await sync_to_async(rooms.first)()
        for user in room.mem_list:
            mem_list.append(user)
        for manager in room.manager_list:
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
            "notice_list": notice_list,
            "is_private": room.is_private
        }))

    async def fetch_message(self, json_info):
        """
        json_info = {
            'msg_id': 124
        }
        """
        msg_id = json_info['msg_id']
        message = await filter_first_message(msg_id=msg_id)
        await self.send(text_data=json.dumps({
            "function": "fetchmessage",
            'msg_id': message.msg_id,
            'msg_type': message.type,
            'msg_time': message.time,
            'msg_body': await async_decode(message.body),
            'sender': message.sender,
            'read_list': message.read_list,
            'delete_list': message.delete_list,
            'combine_list': message.combine_list
        }))

    async def revise_is_notice(self, json_info):
        """
        json_info = {
            chatroom_id: 114514,
            is_notice: True
        }
        """
        function_name = 'revise_is_notice'

        chatroom_id = json_info['chatroom_id']
        chatroom = await self.find_chatroom(function_name, chatroom_id)

        is_notice = json_info['is_notice']

        if chatroom is not None:
            username = await self.get_cur_username()

            user = await self.check_user_exist(function_name, username)

            if user is not None and await self.check_user_in_chatroom(function_name, chatroom, username):
                for index, member_name in enumerate(chatroom.mem_list):
                    if member_name == username:
                        chatroom.is_notice[index] = is_notice

                        await database_sync_to_async(chatroom.save)()
                        await self.send(text_data=json.dumps({
                            'function': function_name,
                            'message': 'Is_Notice Revise Success'
                        }))
                        break

    async def revise_is_top(self, json_info):
        """
        json_info = {
            chatroom_id: 114514,
            is_top: True
        }
        """

        function_name = 'revise_is_top'

        chatroom_id = json_info['chatroom_id']
        is_top = json_info['is_top']
        chatroom = await self.find_chatroom(function_name, chatroom_id)

        if chatroom is not None:
            username = await self.get_cur_username()

            user = await self.check_user_exist(function_name, username)

            if user is not None and await self.check_user_in_chatroom(function_name, chatroom, username):
                for index, member_name in enumerate(chatroom.mem_list):
                    if member_name == username:
                        chatroom.is_top[index] = is_top

                        await database_sync_to_async(chatroom.save)()
                        await self.send(text_data=json.dumps({
                            'function': function_name,
                            'message': 'Is_Top Revise Success'
                        }))
                        break

    async def revise_is_specific(self, json_info):
        """
        json_info = {
            'chatroom_id': 114514,
            'is_specific': True
        }
        """
        username = self.cur_user
        chatroom_id = json_info['chatroom_id']
        is_specific = json_info['is_specific']
        chatroom = await filter_first_chatroom(chatroom_id=chatroom_id)
        idx = await sync_to_async(chatroom.mem_list.index)(username)
        chatroom.is_specific[idx] = is_specific
        await sync_to_async(chatroom.save)()
        await self.send(text_data=json.dumps({
            'function': 'revise_is_specific',
            'message': 'Is_Specific Revise Success'
        }))

    async def examine_password_twice(self, json_info):
        """
        json_info = {
            "password": "114514"
        }
        """
        username = self.cur_user
        password = json_info['password']
        user = await get_user(username=username)
        access = authenticate(username=username, password=password)
        if access:
            await self.send(text_data=json.dumps({
                'function': 'examine_password_twice',
                'access': True
            }))
        else:
            await self.send(text_data=json.dumps({
                'function': 'examine_password_twice',
                'access': False
            }))

    async def remove_manager(self, json_info):
        """
        json_info = {
            'chatroom_id': 114514,
            'manager_name': 'ashitemaru'
        }
        """
        function_name = 'remove_manager'

        chatroom_id = json_info['chatroom_id']
        chatroom = await self.find_chatroom(function_name, chatroom_id)

        if chatroom is not None and not chatroom.is_private:
            username = await self.get_cur_username()
            manager_name = json_info['manager_name']

            if await self.check_chatroom_master(function_name, chatroom, username):
                manager_user = await self.check_user_exist(function_name, manager_name)

                if manager_user is not None and \
                        await self.check_user_in_chatroom(function_name, chatroom, manager_name):
                    if manager_name in chatroom.manager_list:
                        chatroom.manager_list.remove(manager_name)
                        await database_sync_to_async(chatroom.save)()

                        await self.send(text_data=json.dumps({
                            'function': function_name,
                            'message': 'Success'
                        }))
                    else:
                        chatroom.manager_list.append(manager_name)
                        await self.send(text_data=json.dumps({
                            'function': function_name,
                            'message': 'User is not a manager'
                        }))

    async def fetch_invite_list(self, json_info):
        """
        json_info = {
            'username': 'Alice'
        }
        """
        username = json_info['username']
        return_field = []

        async for room in ChatRoom.objects.all():

            await self.send(text_data=json.dumps({
            }))

            if room.is_private:
                continue

            await self.send(text_data=json.dumps({
                "room_name": room.room_name,
                "room_mem: " : str(room.mem_list),
                "user: " : username,
                "room_manager": room.manager_list,
                "room_master": room.master_name
            }))

            if username == room.master_name or username in room.manager_list:
                li = room.mem_list.index(username)

                roomname = room.room_name
                chatroom_id = room.chatroom_id
                room1 = await sync_to_async(ChatRoom.objects.filter)(chatroom_id=chatroom_id)
                room = await sync_to_async(room1.first)()

                power = await get_power(room, username)

                if power == 0:
                    break

                message_list = list()

                invite_list = await get_invite_list(chatroom_id=room.chatroom_id)

                for msg in invite_list.msg_list:
                    cur_message1 = await sync_to_async(Message.objects.filter)(msg_id=msg)
                    cur_message = await sync_to_async(cur_message1.first)()

                    users = await sync_to_async(User.objects.filter)(username=await async_decode(cur_message.body))
                    user = await sync_to_async(users.first)()

                    if user is None:
                        avatar = "/static/media/pic/default.jpeg"
                    else:
                        imusers = await sync_to_async(IMUser.objects.filter)(user=user)
                        imuser = await sync_to_async(imusers.first)()
                        avatar = os.path.join("/static/media/", str(imuser.avatar))
                        if avatar == "/static/media/":
                            avatar += "pic/default.jpeg"

                    message_list.append({
                        "msg_body": await async_decode(cur_message.body),
                        "msg_id": cur_message.msg_id,
                        "msg_type": cur_message.type,
                        "msg_time": cur_message.time,
                        "sender": cur_message.sender,
                        "avatar": avatar,
                        "combine_list": cur_message.combine_list,
                        "read_list": cur_message.read_list,
                        "delete_list": cur_message.delete_list,
                        "msg_answer": cur_message.answer,
                        # "reply_count": cur_message.reply_count
                    })


                return_field.append({
                    "roomid": room.chatroom_id,
                    "roomname": roomname,
                    "is_notice": room.is_notice[li],
                    "is_top": room.is_top[li],
                    "message_list": message_list,
                    "is_private": room.is_private,
                    "is_specific": room.is_specific[li]
                })

        await self.send(text_data=json.dumps({
            "function": "fetchinvitelist",
            "room_list": return_field
        }))

    async def refresh(self, json_info):
        """
        json_info = {
            'friend_list': ['abcdef', 'asdfgh'],
            'chatroom_list': [1, 2], (id)
        }
        """

        chatroom_list = json_info['chatroom_list']
        fetch_list = json_info['friend_list']

        for chatroom_id in chatroom_list:
            chatroom = await filter_first_chatroom(chatroom_id=chatroom_id)

            for username in chatroom.mem_list:
                if username not in fetch_list:
                    fetch_list.append(username)

            timeline = await filter_first_timeline(chatroom_id=chatroom_id)
            if chatroom.is_private:
                await database_sync_to_async(timeline.delete)()
                await database_sync_to_async(chatroom.delete)()
            elif self.cur_user == chatroom.master_name:
                invite_list = await filter_first_invite_list(chatroom_id=chatroom_id)
                await database_sync_to_async(invite_list.delete)()

                await database_sync_to_async(timeline.delete)()
                await database_sync_to_async(chatroom.delete)()


        for index, user in enumerate(CONSUMER_OBJECT_LIST):
            for fetch_name in fetch_list:
                if user.cur_user == fetch_name:
                    await CONSUMER_OBJECT_LIST[index].fetch_invite_list({"username": fetch_name})
                    await CONSUMER_OBJECT_LIST[index].fetch_room({"username": fetch_name})
                    await CONSUMER_OBJECT_LIST[index].fetch_friend_list({"username": fetch_name})
                    break

        await self.send(text_data=json.dumps({
            "function": "refresh",
            "message": "Success"
        }))

