from channels.db import database_sync_to_async
from django.contrib.auth.models import User

import Chat.models
import FriendRelation.models


@database_sync_to_async
def get_user(username):
    return User.objects.get(username=username)


@database_sync_to_async
def get_user_id(username):
    return User.objects.get(username=username).id


@database_sync_to_async
def get_addlist(username):
    return FriendRelation.models.AddList.objects.get(user_name=username)


@database_sync_to_async
def get_friendlist(username):
    return FriendRelation.models.FriendList.objects.get(user_name=username)


@database_sync_to_async
def get_timeline(chatroom_id=None, timeline_id=None):
    """
    只填一个即可
    """
    if chatroom_id is None:
        if timeline_id is None:
            return None
        else:
            return Chat.models.ChatTimeLine.objects.get(timeline_id=timeline_id)
    else:
        return Chat.models.ChatTimeLine.objects.get(chatroom_id=chatroom_id)


@database_sync_to_async
def filter_first_addlist(username):
    return FriendRelation.models.AddList.objects.filter(user_name=username).first()


@database_sync_to_async
def filter_first_chatroom(chatroom_id=None, timeline_id=None):
    """
    只填一个即可
    """
    if chatroom_id is None:
        if timeline_id is None:
            return None
        else:
            return Chat.models.ChatRoom.objects.filter(timeline_id=chatroom_id).first()
    else:
        return Chat.models.ChatRoom.objects.filter(chatroom_id=timeline_id).first()


@database_sync_to_async
def filter_first_timeline(chatroom_id=None, timeline_id=None):
    """
    只填一个即可
    """
    if chatroom_id is None:
        if timeline_id is None:
            return None
        else:
            return Chat.models.ChatTimeLine.objects.filter(chatroom_id=chatroom_id).first()
    else:
        return Chat.models.ChatTimeLine.objects.filter(timeline_id=timeline_id).first()


@database_sync_to_async
def filter_first_onlineuser(username):
    return Chat.models.OnlineUser.objects.filter(user_name=username).first()


@database_sync_to_async
def filter_first_message(msg_id):
    return Chat.models.Message.objects.filter(msg_id=msg_id).first()

@database_sync_to_async
def filter_first_friend(user_name,friend_name):
    return FriendRelation.models.Friend.objects.filter(friend_name=friend_name, user_name=user_name).first()