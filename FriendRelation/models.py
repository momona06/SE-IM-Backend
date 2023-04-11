from django.db import models
from django.contrib.postgres.fields import ArrayField

# friend of a imuser
class Friend(models.Model):
    user_name = models.CharField(max_length=100) # owner of the friend
    friend_name = models.CharField(max_length=100)
    group_name = models.CharField(max_length=100)

# friendlist of a imuser
class FriendList(models.Model):
    user_name = models.CharField(max_length=100,default='username')

    group_list = ArrayField(
        models.CharField(max_length=100)
    )

    friend_list = ArrayField(
        ArrayField(
            models.CharField(max_length=100) # friend_name
        )
    )

class AddList(models.Model):
    user_name = models.CharField(max_length=100,default='username')

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


