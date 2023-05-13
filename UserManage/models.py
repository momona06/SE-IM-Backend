from django.db import models
from django.contrib.auth.models import User


def create_im_user(user, token):
    im_user = IMUser(user=user, token=token)
    im_user.save()
    return im_user


class IMUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # is_login = models.BooleanField(default=False)
    token = models.CharField(max_length=100)
    # avatar = models.ImageField(upload_to='avatar/%Y%m%d/', blank=True)


class TokenPoll(models.Model):
    token = models.CharField(max_length=100)


class EmailCode(models.Model):
    email = models.EmailField(max_length=50, verbose_name="邮箱")
    code = models.CharField(max_length=20, verbose_name="验证码")
