from django.db import models
from django.contrib.auth.models import User
from UserManage.models import IMUser, TokenPoll, CreateIMUser



class FriendGroup(models.Model):
    fgroup_name = models.CharField(max_length=100)

class Test(models.Model):
    ffg = models.CharField(max_length=3)
    rely = models.CharField(max_length=43,default="re")
