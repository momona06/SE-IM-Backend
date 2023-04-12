from django.db import models
from django.contrib.auth.models import User

def CreateIMUser(user, token, **extra_fields):
    im_user = IMUser(user=user, token=token, **extra_fields)
    im_user.save()
    return im_user


class IMUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=100)


class TokenPoll(models.Model):
    token = models.CharField(max_length=100)
