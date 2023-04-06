from django.db import models
from django.contrib.auth.models import User
from UserManage.models import IMUser, TokenPoll, CreateIMUser



class FriendGroup(models.Model):
    fgroup_name = models.CharField(max_length=100)
