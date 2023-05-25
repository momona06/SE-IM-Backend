from django.db import models
from django.contrib.postgres.fields import ArrayField


# friend of an imuser
class Friend(models.Model):
    # owner of the friend
    user_name = models.CharField(
        max_length=100
    )
    friend_name = models.CharField(
        max_length=100
    )
    group_name = models.CharField(
        max_length=100
    )


# friendlist of an imuser
class FriendList(models.Model):
    user_name = models.CharField(
        max_length=100,
        default='username'
    )

    group_list = ArrayField(
        models.CharField(max_length=100)
    )

    friend_list = ArrayField(
        models.CharField(max_length=100)
    )


class AddList(models.Model):
    user_name = models.CharField(
        max_length=100,
        default='username'
    )

    # reply for adding request
    reply_list = ArrayField(
        models.CharField(max_length=100)
    )
    # answer for reply
    reply_answer = ArrayField(
        models.BooleanField(default=False)
    )
    # ensure the reply or not
    reply_ensure = ArrayField(
        models.BooleanField(default=False)
    )

    # apply for adding new friend
    apply_list = ArrayField(
        models.CharField(max_length=100)
    )
    # answer for apply
    apply_answer = ArrayField(
        models.BooleanField(default=False)
    )

    apply_ensure = ArrayField(
        models.BooleanField(default=False)
    )
