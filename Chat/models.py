from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from django.db import models
from django.contrib.postgres.fields import ArrayField


@database_sync_to_async
def filter_first_chatroom(chatroom_id=None, timeline_id=None):
    """
    只填一个即可
    """
    if chatroom_id is None:
        if timeline_id is None:
            return None
        else:
            return ChatRoom.objects.filter(timeline_id=timeline_id).first()
    else:
        return ChatRoom.objects.filter(chatroom_id=chatroom_id).first()


# Design philosophy: remove info about the chatroom and only reserve the necessary info
# Timeline for storage owned by a specific chatroom
# Viewed As Storage Database
class ChatTimeLine(models.Model):
    timeline_id = models.BigAutoField(primary_key=True)
    chatroom_id = models.BigIntegerField(default=0)

    # meg id list
    msg_line = ArrayField(
        models.BigIntegerField(default=0)
    )

    # represent the message showed on the frontend of each user
    cursor_list = ArrayField(
        models.BigIntegerField(default=0)
    )


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


async def create_chatroom(room_name, mem_list, master_name, is_private=False):
    """
    参考：room_name='private_chat'
    """
    mem_len = len(mem_list)
    true_mem_len_list = [True for _ in range(mem_len)]
    false_mem_len_list = [False for _ in range(mem_len)]
    new_chatroom = await database_sync_to_async(ChatRoom)(is_private=is_private, room_name=room_name,
                                                          mem_count=mem_len, mem_list=mem_list,
                                                          master_name=master_name, manager_list=[],
                                                          is_notice=true_mem_len_list, is_top=false_mem_len_list,
                                                          notice_id=0, notice_list=[])
    await database_sync_to_async(new_chatroom.save)()

    timeline = await database_sync_to_async(ChatTimeLine)(chatroom_id=new_chatroom.chatroom_id, msg_line=[],
                                                          cursor_list=[])
    timeline.cursor_list = [0 for _ in range(mem_len)]
    await database_sync_to_async(timeline.save)()

    new_chatroom.timeline_id = timeline.timeline_id
    timeline.chatroom_id = new_chatroom.chatroom_id
    await database_sync_to_async(new_chatroom.save)()
    await database_sync_to_async(timeline.save)()
    return new_chatroom


async def delete_chatroom():
    pass


# Design philosophy: all info about the message itself should be put here
class Message(models.Model):
    msg_id = models.BigAutoField(primary_key=True)

    # type = {text, image, file, video, audio, combine, reply, invite, notice}
    type = models.CharField(max_length=20)

    # invite type, -1: no answer 0: decline 1: confirm
    answer = models.IntegerField(default=-1)

    # msg for {text, reply}
    body = models.CharField(max_length=500)

    # src for image, file, video, audio
    # src = models.FileField(upload_to=user_directory_path, blank=True, null=True)

    # related msg for {reply}
    reply_id = models.BigIntegerField(default=0)

    # list for those who read this message
    read_list = ArrayField(
        models.BooleanField(default=False)
    )

    # list for combined message
    combine_list = ArrayField(
        models.BigIntegerField(default=0)
    )

    time = models.CharField(max_length=100)

    sender = models.CharField(max_length=100)


async def create_message(type, body, time, sender, reply_id=0, answer=-1, read_list=[], combine_list=[]):
    new_message = await database_sync_to_async(Message)(type=type, body=body, time=time,
                                                        sender=sender, reply_id=reply_id, answer=answer,
                                                        read_list=read_list, combine_list=combine_list)
    await database_sync_to_async(new_message.save)()
    return new_message


async def delete_message():
    """
    json_info = {
    }
    """
    pass
