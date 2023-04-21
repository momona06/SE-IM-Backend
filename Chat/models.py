from django.db import models
from django.contrib.postgres.fields import ArrayField

# timeline for storage owned by a specific chatroom
# Storage Database
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
# Sync Database

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


# a specific public chatroom
class PublicChatRoom(models.Model):
    chatroom_id = models.BigAutoField(primary_key=True)
    room_name = models.CharField(max_length=30)

    mem_count = models.BigIntegerField(default=2)
    mem_list = ArrayField(
        models.CharField(max_length=100)
    )



# members owned by a specific chatroom
# class ChatRoomMemberList(models.Model):
#     memlist_id = models.BigAutoField(primary_key=True)
#     pcr_id = models.BigIntegerField(default=0)
    # is_private = models.BooleanField(default=False)


# a specific message
class Message(models.Model):
    msg_id = models.BigAutoField(primary_key=True)
    type = models.CharField(max_length=20)
    body = models.CharField(max_length=500)
    time = models.CharField(max_length=100)




