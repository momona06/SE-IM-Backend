from django.db import models
from django.contrib.auth.models import User


def create_im_user(user, token, is_login=False, **extra_fields):
    im_user = IM_User(user=user, token=token, is_login=is_login, **extra_fields)
    im_user.save()
    return im_user

class IM_User(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=100)
    is_login = models.BooleanField(default=False)

class Token_Poll(models.Model):
    token = models.CharField(max_length=100)
