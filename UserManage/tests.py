from django.test import TestCase

from Chat.models import ChatRoom, InviteList, Message, ChatTimeLine
from UserManage.models import IMUser
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from FriendRelation.models import FriendList, AddList, Friend
import json
import random

from utils.utils_cryptogram import encode

PAS = "123456"
USERNAME = "test00"

def create_message(body,sender,time='2023-05-24 23:59:59',type='text', reply_id=0, reply_count=0, answer=-1, read_list=None, combine_list=None,
                         delete_list=None):

    if combine_list is None:
        combine_list = list()
    if read_list is None:
        read_list = list()
    if delete_list is None:
        delete_list = list()
    body = encode(body)
    new_message = Message(type=type, body=body, time=time, sender=sender,
                                                        reply_count=reply_count, reply_id=reply_id, answer=answer,
                                                        delete_list=delete_list, read_list=read_list, combine_list=combine_list)
    new_message.save()
    return new_message

def sync_create_chatroom(room_name, mem_list, master_name, is_private=False):
    """
    参考：room_name='private_chat'
    """
    mem_len = len(mem_list)
    true_mem_len_list = [True for _ in range(mem_len)]
    false_mem_len_list = [False for _ in range(mem_len)]
    new_chatroom = ChatRoom(is_private=is_private, room_name=room_name,
                                                          mem_count=mem_len, mem_list=mem_list,
                                                          master_name=master_name, manager_list=[],
                                                          is_notice=true_mem_len_list, is_top=false_mem_len_list,
                                                          is_specific=false_mem_len_list, notice_id=0, notice_list=[])
    new_chatroom.save()

    timeline = ChatTimeLine(chatroom_id=new_chatroom.chatroom_id, msg_line=[],
                                                          cursor_list=[])
    timeline.cursor_list = [0 for _ in range(mem_len)]
    timeline.save()

    invite_list = InviteList(chatroom_id=new_chatroom.chatroom_id, msg_list=[])
    invite_list.save()

    new_chatroom.timeline_id = timeline.timeline_id
    timeline.chatroom_id = new_chatroom.chatroom_id

    new_chatroom.invite_list_id = invite_list.invite_list_id

    new_chatroom.save()
    timeline.save()
    return new_chatroom


class UserManageTest(TestCase):
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

    def user_revise(self, revise_field, revise_content, username, input_password, token):
        payload = {
            "revise_field": revise_field,
            "revise_content": revise_content,
            "username": username,
            "input_password": input_password,
            "token": token
        }
        return self.client.put("/user/revise", data=payload, content_type="application/json")

    def user_send_email(self, email):
        payload = {
            "email": email
        }
        return self.client.post("/user/send_email", data=payload, content_type="application/json")

    def user_bind_email(self, email, code, username):
        payload = {
            "email": email,
            "code": code,
            "username": username
        }
        return self.client.post("/user/email", data=payload, content_type="application/json")

    def test_register(self):
        # username = secrets.token_hex(4)
        # password = secrets.token_hex(4)

        self.user_cancel(USERNAME, PAS)
        res = self.user_register(USERNAME, PAS)

        self.assertJSONEqual(res.content, {"code": 0, "info": "Register Succeed"})
        self.assertEqual(res.json()["code"], 0)
        user_model = get_user_model()
        user = user_model.objects.filter(username=USERNAME).first()
        self.assertTrue(user_model.objects.filter(username=USERNAME).exists())
        self.assertTrue(IMUser.objects.filter(user=user).exists())

    def test_login_logout(self):
        # username = secrets.token_hex(10)
        # password = secrets.token_hex(10)

        self.user_cancel(USERNAME, PAS)
        res_reg = self.user_register(USERNAME, PAS)
        res_lin = self.user_login(USERNAME, PAS)
        self.assertEqual(res_reg.json()["code"], 0)
        self.assertEqual(res_lin.json()["code"], 0)
        user_model = get_user_model()
        self.assertTrue(user_model.objects.filter(username=USERNAME).exists())

        user = user_model.objects.filter(username=USERNAME).first()
        im_user = IMUser.objects.filter(user=user).first()

        token = res_lin.json()["token"]
        res_lout = self.user_logout(USERNAME, token)
        im_user = IMUser.objects.filter(user=user).first()
        self.assertEqual(res_lout.json()["code"], 0)

    def test_cancel(self):
        # username = secrets.token_hex(10)
        # password = secrets.token_hex(10)
        self.user_cancel(USERNAME, PAS)
        input_password = PAS

        res_reg = self.user_register(USERNAME, PAS)
        res_lin = self.user_login(USERNAME, PAS)
        self.assertEqual(res_lin.json()["code"], 0)

        token_0 = res_lin.json()["token"]

        user_model = get_user_model()
        self.assertTrue(user_model.objects.filter(username=USERNAME).exists())
        user = user_model.objects.filter(username=USERNAME).first()
        im_user = IMUser.objects.filter(user=user).first()

        USERNAME_1 = '1234567'

        self.user_register(USERNAME_1, PAS)
        res_lin_1 = self.user_login(USERNAME_1, PAS)

        token_1 = res_lin_1.json()["token"]

        addlist_0 = AddList.objects.get(user_name=USERNAME)
        friendlist_0 = FriendList.objects.get(user_name=USERNAME)

        addlist_0.apply_list.append(USERNAME_1)
        addlist_0.apply_answer.append(True)
        addlist_0.apply_ensure.append(True)

        addlist_0.save()

        addlist_1 = AddList.objects.get(user_name=USERNAME_1)
        friendlist_1 = FriendList.objects.get(user_name=USERNAME_1)

        addlist_1.reply_list.append(USERNAME)
        addlist_1.reply_answer.append(True)
        addlist_1.reply_ensure.append(True)

        addlist_1.save()

        friend_0 = Friend(user_name=USERNAME, friend_name=USERNAME_1, group_name=friendlist_0.group_list[0])
        friend_0.save()

        friend_1 = Friend(user_name=USERNAME_1, friend_name=USERNAME, group_name=friendlist_1.group_list[0])
        friend_1.save()

        chatroom = sync_create_chatroom('private_chat', [USERNAME, USERNAME_1], USERNAME, is_private=True)
        chatroom.save()

        read_list = [False, False]

        message = create_message(body='1234', sender=USERNAME, read_list=read_list)
        message.save()

        timeline = ChatTimeLine.objects.get(chatroom_id=chatroom.chatroom_id)
        timeline.msg_line.append(message.msg_id)
        timeline.save()

        chatroom_group = sync_create_chatroom('111', [USERNAME, USERNAME_1], USERNAME, is_private=False)
        chatroom_group.save()

        invite_message = create_message(type='invite',body='111',sender=USERNAME, read_list=read_list)
        invite_message.save()

        message_group = create_message(body='123', sender=USERNAME, read_list=read_list)
        message_group.save()

        timeline_group = ChatTimeLine.objects.get(chatroom_id=chatroom_group.chatroom_id)
        timeline_group.msg_line.append(invite_message.msg_id)
        timeline_group.msg_line.append(message_group.msg_id)
        timeline_group.save()

        invite_list = InviteList.objects.get(chatroom_id=chatroom_group.chatroom_id)
        invite_list.msg_list.append(invite_message.msg_id)
        invite_list.save()

        res_cel = self.user_cancel(USERNAME, input_password)
        self.assertFalse(user_model.objects.filter(username=USERNAME).exists())

        self.assertFalse(Friend.objects.filter(user_name=USERNAME).exists())
        self.assertFalse(Friend.objects.filter(friend_name=USERNAME).exists())

        self.assertFalse(AddList.objects.filter(user_name=USERNAME).exists())
        self.assertEqual(0, len(AddList.objects.get(user_name=USERNAME_1).reply_list))
        self.assertEqual(0, len(AddList.objects.get(user_name=USERNAME_1).reply_answer))
        self.assertEqual(0, len(AddList.objects.get(user_name=USERNAME_1).reply_ensure))

        self.assertTrue(ChatRoom.objects.filter(master_name=USERNAME).exists())

        self.assertFalse(ChatRoom.objects.filter(mem_list=[USERNAME, USERNAME_1]).exists())
        self.assertTrue(ChatRoom.objects.filter(mem_list=[USERNAME_1]).exists())

        self.assertEqual('AccountSuspended',Message.objects.get(msg_id=message_group.msg_id).sender)
        self.assertEqual(USERNAME,Message.objects.get(msg_id=message.msg_id).sender)
        self.assertEqual(2, len(Message.objects.get(msg_id=message_group.msg_id).read_list))

    def test_revise(self):
        # username = secrets.token_hex(10)
        # password = secrets.token_hex(10)

        USERNAME = '123123'

        input_password = PAS
        res_reg = self.user_register(USERNAME, PAS)
        res_lin = self.user_login(USERNAME, PAS)
        self.assertEqual(res_reg.json()["code"], 0)
        self.assertEqual(res_lin.json()["code"], 0)

        user_model = get_user_model()
        self.assertTrue(user_model.objects.filter(username=USERNAME).exists())
        user = user_model.objects.filter(username=USERNAME).first()
        im_user = IMUser.objects.filter(user=user).first()

        token = res_lin.json()['token']

        # no email yet
        revise_field_list = ["username", "password"]
        revise_content_list = ["321321", "1234567"]
        # for field, content in zip(revise_field_list, revise_content_list):
        res_rev = self.user_revise(revise_field_list[1], revise_content_list[1], USERNAME, input_password, token)
        self.assertEqual(res_rev.json()["code"], 0)
        print(res_rev.json())
        # self.assertEqual(res_rev.json()["info"],"dd")

        self.user_revise(revise_field_list[1], input_password, USERNAME, revise_content_list[1], token)
        token = res_lin.json()["token"]

        USERNAME = '321321'

        self.user_register(USERNAME, PAS)
        res_lin = self.user_login(USERNAME, PAS)
        token = res_lin.json()["token"]

        USERNAME_1 = '1234567'

        self.user_register(USERNAME_1, PAS)
        res_lin_1 = self.user_login(USERNAME_1, PAS)

        token_1 = res_lin_1.json()["token"]

        addlist_0 = AddList.objects.get(user_name=USERNAME)
        friendlist_0 = FriendList.objects.get(user_name=USERNAME)

        addlist_0.apply_list.append(USERNAME_1)
        addlist_0.apply_answer.append(True)
        addlist_0.apply_ensure.append(True)

        addlist_0.save()

        addlist_1 = AddList.objects.get(user_name=USERNAME_1)
        friendlist_1 = FriendList.objects.get(user_name=USERNAME_1)

        addlist_1.reply_list.append(USERNAME)
        addlist_1.reply_answer.append(True)
        addlist_1.reply_ensure.append(True)

        addlist_1.save()

        friend_0 = Friend(user_name=USERNAME, friend_name=USERNAME_1, group_name=friendlist_0.group_list[0])
        friend_0.save()

        friend_1 = Friend(user_name=USERNAME_1, friend_name=USERNAME, group_name=friendlist_1.group_list[0])
        friend_1.save()

        chatroom = sync_create_chatroom('private_chat', [USERNAME, USERNAME_1], USERNAME, is_private=True)
        chatroom.save()

        read_list = [False, False]

        message = create_message(body='1234', sender=USERNAME, read_list=read_list)
        message.save()

        timeline = ChatTimeLine.objects.get(chatroom_id=chatroom.chatroom_id)
        timeline.msg_line.append(message.msg_id)
        timeline.save()

        chatroom_group = sync_create_chatroom('111', [USERNAME, USERNAME_1], USERNAME, is_private=False)
        chatroom_group.save()

        invite_message = create_message(type='invite',body='111',sender=USERNAME, read_list=read_list)
        invite_message.save()

        message_group = create_message(body='123', sender=USERNAME, read_list=read_list)
        message_group.save()

        timeline_group = ChatTimeLine.objects.get(chatroom_id=chatroom_group.chatroom_id)
        timeline_group.msg_line.append(invite_message.msg_id)
        timeline_group.msg_line.append(message_group.msg_id)
        timeline_group.save()

        invite_list = InviteList.objects.get(chatroom_id=chatroom_group.chatroom_id)
        invite_list.msg_list.append(invite_message.msg_id)
        invite_list.save()

        self.user_revise(revise_field_list[0], revise_content_list[0], USERNAME, input_password, token)

        self.assertFalse(User.objects.filter(username=USERNAME).exists())
        self.assertTrue(User.objects.filter(username=revise_content_list[0]).exists())

        self.assertFalse(Friend.objects.filter(user_name=USERNAME).exists())
        self.assertFalse(Friend.objects.filter(friend_name=USERNAME).exists())
        self.assertTrue(Friend.objects.filter(user_name=revise_content_list[0]).exists())
        self.assertTrue(Friend.objects.filter(friend_name=revise_content_list[0]).exists())

        self.assertFalse(AddList.objects.filter(user_name=USERNAME).exists())
        self.assertTrue(AddList.objects.filter(user_name=revise_content_list[0]).exists())

        self.assertEqual(revise_content_list[0], AddList.objects.get(user_name=USERNAME_1).reply_list[0])

        self.assertFalse(ChatRoom.objects.filter(master_name=USERNAME).exists())
        self.assertTrue(ChatRoom.objects.filter(master_name=revise_content_list[0]).exists())

        self.assertFalse(ChatRoom.objects.filter(mem_list=[USERNAME, USERNAME_1]).exists())

        self.assertEqual(revise_content_list[0],Message.objects.get(msg_id=message_group.msg_id).sender)
        self.assertEqual(revise_content_list[0],Message.objects.get(msg_id=message.msg_id).sender)


    def test_email(self):
        username = USERNAME
        password = PAS
        self.user_register(username, password)
        email = "zhoujin@mails.tsinghua.edu.cn"
        res = self.user_send_email(email)
        # res = self.userBindEmail(email,res_sms_code,username)
        self.assertEqual(res.json()["code"], 0)
