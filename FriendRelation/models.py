from django.db import models

from django.contrib.postgres.fields import ArrayField

# friend of a imuser
class Friend(models.Model):
    user_name = models.CharField(max_length=100) # owner of the friend
    friend_name = models.CharField(max_length=100)
    group_name = models.CharField(max_length=100)

# friendlist of a imuser
class FriendList(models.Model):
    user_name = models.CharField(max_length=100)

    group_list = ArrayField(
        models.CharField(max_length=100)
    )

    friend_list = ArrayField(
        ArrayField(
            #models.OneToOneField(Friend, on_delete=models.CASCADE)
            models.CharField(max_length=100) # friend_name
        )
    )



