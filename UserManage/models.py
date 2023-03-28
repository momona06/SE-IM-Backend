from django.db import models

class User(models.Model):
    id = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=50)
    password = models.CharField(max_length=50)

    def serialize(self):
        return {
            "id": self.id,
            "username": self.username,
            "password": self.password
        }

    def __str__(self):
        return "id = " + self.id + " username = " + self.username + " password = " + self.password