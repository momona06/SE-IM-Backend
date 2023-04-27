from asgiref.sync import sync_to_async
from django.db import models
from django.contrib.postgres.fields import ArrayField

from channels.db import database_sync_to_async


async def create_chat_timeline():
    new_timeline = ChatTimeLine()
    await sync_to_async(new_timeline.save)()
    return new_timeline


async def delete_chat_timeline():
    pass


# Design philosophy: remove info about the chatroom and only reserve the necessary info

# timeline for storage owned by a specific chatroom
# Viewed As Storage Database
class ChatTimeLine(models.Model):
    timeline_id = models.BigAutoField(primary_key=True)

    # is_private = models.BooleanField(default=False)
    chatroom_id = models.BigIntegerField(default=0)

    msg_line = ArrayField(
        models.BigIntegerField(default=0)
    )

    cursor_list = ArrayField(
        models.BigIntegerField(default=0)
    )


# timeline for sync owned by a specific user
# Viewed As Sync Database
# class UserTimeLine(models.Model):
#     utl_id = models.BigAutoField(primary_key=True)
#
#     owner = models.CharField(max_length=100)
#
#     cursor = models.BigIntegerField(default=0)
#     msg_line = ArrayField(
#         models.BigIntegerField(default=0)
#     )


# a specific private chatroom example
# class PrivateChatRoom(models.Model):
#     pcr_id = models.BigAutoField(primary_key=True)
#     room_name = models.CharField(max_length=30)
#
#     im_user1 = models.CharField(max_length=100)
#     im_user2 = models.CharField(max_length=100)


async def create_chatroom(room_name, mem_list, master_name, is_private=False, is_notice=True, is_top=False):
    new_chatroom = ChatRoom(is_private=is_private, room_name=room_name,
                            mem_count=len(mem_list), mem_list=mem_list,
                            is_notice=is_notice, is_top=is_top,
                            master_name=master_name, manager_list=[],
                            notice_id=0, notice_list=[])
    await sync_to_async(new_chatroom.save)()
    return new_chatroom


async def delete_chatroom():
    # ondel_chatroom = ChatRoom.objects.filter()
    pass

# Design philosophy: all info about the message itself should be put here

# a specific message
class Message(models.Model):
    msg_id = models.BigAutoField(primary_key=True)

    # room_id = models.BigIntegerField(default=0)
    # timeline_id = models.BigIntegerField(default=0)

    type = models.CharField(max_length=20)
    body = models.CharField(max_length=500)
    time = models.CharField(max_length=100)
    sender = models.CharField(max_length=100)
    is_reply = models.BooleanField(default=False)
    rel_id = models.BigIntegerField(default=0)

    is_read = ArrayField(
        models.BooleanField(default=False)
    )
# Design philosophy: all the info about the room should be put here
# Pay attention: Public and Private Chatroom classified by the field 'is_private'

# a specific chatroom
class ChatRoom(models.Model):
    chatroom_id = models.BigAutoField(primary_key=True)

    #timeline_id = models.BigIntegerField(default=0)

    # mark the same room_name case
    # dup_id = models.BigIntegerField(default=0)

    # a chatroom must own a specified room_name
    room_name = models.CharField(max_length=30, default='private_chat')

    is_private = models.BooleanField(default=True)

    mem_count = models.BigIntegerField(default=2)

    mem_list = ArrayField(
        models.CharField(max_length=100)
    )
    not_read = ArrayField(
        models.IntegerField(default=0)
    )

    is_notice = ArrayField(
        models.BooleanField(default=True)
    )

    is_top = ArrayField(
        models.BooleanField(default=False)
    )

    master_name = models.CharField(max_length=100, default='master')

    manager_list = ArrayField(
        models.CharField(max_length=100)
    )
    mes_list = ArrayField(
         models.BigIntegerField(default=0)
    )
    notice_id = models.BigIntegerField(default=0)

    notice_list = ArrayField(
        models.BigIntegerField(default=0)
    )


# members owned by a specific chatroom
# class ChatRoomMemberList(models.Model):
#     memlist_id = models.BigAutoField(primary_key=True)
#     pcr_id = models.BigIntegerField(default=0)
#     is_private = models.BooleanField(default=False)


def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return "user_{0}/{1}".format(instance.user.id)


# Design philosophy: all info about the message itself should be put here

# a specific message

def create_message(type, body, time, sender, is_reply = False, rel_id = 0):
    new_message = Message(type = type, body = body, time = time, sender = sender,is_reply = is_reply, rel_id = rel_id)
    new_message.save()
    return new_message


class OnlineUser(models.Model):
    user_name = models.CharField(max_length=100)
    channel_name = models.CharField(max_length=1000)
    chatroom_id = models.BigIntegerField(default=0)

async def create_onlineuser(user_name, channel_name, room_id):
    new_onliner = await database_sync_to_async(OnlineUser)(user_name=user_name, channel_name=channel_name, chatroom_id=room_id)
    new_onliner.save()
    return new_onliner
