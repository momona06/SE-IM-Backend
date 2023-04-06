from django.db import models
from django.contrib.auth.models import User
from UserManage.models import IMUser, TokenPoll, CreateIMUser



#class FriendGroup(models.Model):
#    fgroup_name = models.CharField(max_length=100)


class FriendList(models.Model):
    user_name = models.CharField(max_length=100)

class Friend(models.Model):
    user_name = models.CharField(max_length=100)
    friend_name = models.CharField(max_length=100)
    group_name = models.CharField(max_length=100)
    list = models.ForeignKey(FriendList, on_delete=models.CASCADE)

