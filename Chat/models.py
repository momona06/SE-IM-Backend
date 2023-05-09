from asgiref.sync import sync_to_async
from django.db import models
from django.contrib.postgres.fields import ArrayField

from channels.db import database_sync_to_async

from utils.utils_database import filter_first_chatroom


# Design philosophy: remove info about the chatroom and only reserve the necessary info
# Timeline for storage owned by a specific chatroom
# Viewed As Storage Database
class ChatTimeLine(models.Model):
    timeline_id = models.BigAutoField(primary_key=True)
    chatroom_id = models.BigIntegerField(default=0)

    msg_line = ArrayField(
        models.BigIntegerField(default=0)
    )

    # represent the message showed on the frontend of each user
    cursor_list = ArrayField(
        models.BigIntegerField(default=0)
    )

    is_read = ArrayField(
        ArrayField(
            models.BooleanField(default=False)
        )
    )

async def create_chat_timeline(chatroom_id):
    chatroom = await filter_first_chatroom(chatroom_id=chatroom_id)
    mem_len = len(chatroom.mem_list)

    new_timeline = await database_sync_to_async(ChatTimeLine)(chatroom_id=chatroom_id, msg_line=[], cursor_list=[], is_read=[])
    for _ in range(mem_len):
        new_timeline.cursor_list.append(0)
    await sync_to_async(new_timeline.save)()

    return new_timeline


async def delete_chat_timeline():
    pass










# Design philosophy: all the info about the room should be put here
class ChatRoom(models.Model):
    chatroom_id = models.BigAutoField(primary_key=True)

    timeline_id = models.BigIntegerField(default=0)

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

    notice_id = models.BigIntegerField(default=0)
    notice_list = ArrayField(
        models.BigIntegerField(default=0)
    )

async def create_chatroom(room_name, mem_list, master_name, is_private=False, is_notice=True, is_top=False):
    new_chatroom = await database_sync_to_async(ChatRoom)(is_private=is_private, room_name=room_name,
                            mem_count=len(mem_list), mem_list=mem_list,
                            is_notice=is_notice, is_top=is_top,
                            master_name=master_name, manager_list=[],
                            notice_id=0, notice_list=[])
    await sync_to_async(new_chatroom.save)()
    return new_chatroom


async def delete_chatroom():
    pass







# Design philosophy: all info about the message itself should be put here
class Message(models.Model):
    msg_id = models.BigAutoField(primary_key=True)

    # type = {text, image, file, video, audio, combine, reply, invite}
    type = models.CharField(max_length=20)

    # msg for {text, reply}
    body = models.CharField(max_length=500)

    # src for image, file, video, audio
    # src = models.FileField(upload_to=user_directory_path, blank=True, null=True)

    # related msg for {reply}
    reply_id = models.BigIntegerField(default=0)


    time = models.CharField(max_length=100)
    sender = models.CharField(max_length=100)


def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return "user_{0}/{1}".format(instance.user.id)



async def create_message(type, body, time, sender, is_reply=False, reply_id=0):
    new_message = await database_sync_to_async(Message)(type=type, body=body, time=time, sender=sender, is_reply=is_reply, reply_id=reply_id)
    new_message.save()
    return new_message

async def delete_message():
    pass






# Users in chatrooms
class OnlineUser(models.Model):
    user_name = models.CharField(max_length=100)
    channel_name = models.CharField(max_length=1000)
    chatroom_id = models.BigIntegerField(default=0)


async def create_onlineuser(user_name, channel_name, room_id):
    new_onliner = await database_sync_to_async(OnlineUser)(user_name=user_name, channel_name=channel_name, chatroom_id=room_id)
    new_onliner.save()
    return new_onliner

async def delete_onlineuser(user_name):
    await sync_to_async(OnlineUser.objects.filter(user_name=user_name).delete)()