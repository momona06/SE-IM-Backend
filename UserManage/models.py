from django.db import models
from django.contrib.auth.models import User

def CreateIMUser(user, token, is_login=False, **extra_fields):
    im_user = IMUser(user=user, token=token, is_login=is_login, **extra_fields)
    im_user.save()
    return im_user


class IMUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=100)
    is_login = models.BooleanField(default=False)




class TokenPoll(models.Model):
    token = models.CharField(max_length=100)
