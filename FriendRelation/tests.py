from django.test import TestCase
from django.contrib.auth import get_user_model
import json
import random

from django.contrib.auth.models import User
from UserManage.models import IMUser


class FriendRelationTest(TestCase):
    def userCheck(self, my_username,check_name, token):
        payload = {
            "username": my_username,
            "password": check_name,
            "token": token,
        }
        return self.client.post("/friend/checkuser", data=payload, content_type="application/json")


    def userSearch(self, my_username, search_username):
        payload = {
            "username": my_username,
            "password": search_username,
        }
        return self.client.post("/friend/searchuser", data=payload, content_type="application/json")

    def testCheckUser(self):
        pass

    def testSearchUser(self):
        pass