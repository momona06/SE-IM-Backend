import json
import random

from django.test import TestCase
from django.contrib.auth import get_user_model

from django.contrib.auth.models import User
from UserManage.models import IMUser


class FriendRelationTest(TestCase):

    def friend_group_add(self):
        pass

    def friend_list_get(self):
        pass

    def add_friend_to_group(self):
        pass


    def friend_delete(self):
        pass

    def friend_group_delete(self):
        pass


    def test_fgroup_add(self):
        pass

    def test_flist_get(self):
        pass

    def test_friend_to_group(self):
        pass

    def test_delete_friend(self):
        pass

    def test_delete_fgroup(self):
        pass




    # nzh code
    def user_register(self, username, password):
        payload = {
            "username": username,
            "password": password
        }
        return self.client.post("/user/register", data=payload, content_type="application/json")

    def user_login(self, username, password, email=""):
        payload = {
            "username": username,
            "password": password,
            "email": email
        }
        return self.client.post("/user/login", data=payload, content_type="application/json")

    def user_check(self, my_username, check_name, token):
        payload = {
            "my_username": my_username,
            "check_name": check_name,
            "token": token,
        }
        return self.client.post("/friend/checkuser", data=payload, content_type="application/json")

    def user_search(self, my_username, search_username):
        payload = {
            "username": my_username,
            "search_username": search_username,
        }
        return self.client.post("/friend/searchuser", data=payload, content_type="application/json")


    def test_check_user(self):
        username = random.randint(100_000_000_000, 999_999_999_999)
        password = random.randint(100_000_000_000, 999_999_999_999)

        username_1 = username
        password_1 = random.randint(100_000_000_000, 999_999_999_999)

        self.user_register(username, password)
        res_login = self.user_login(username, password)

        token = res_login.json()["token"]

        res_check = self.user_check(username, username_1, token)
        self.assertEqual(res_check.json()["code"], -4)

        username_1 = username + 1

        self.user_register(username_1, password_1)
        user_model = get_user_model()
        self.assertTrue(user_model.objects.filter(username=username_1).exists())

        res_check = self.user_check(username, username_1, token)
        self.assertEqual(res_check.json()["code"], 0)

        res_check = self.user_check(username - 1, username_1, token)
        self.assertEqual(res_check.json()["code"], -3)

        res_check = self.user_check(username, username_1 + 1, token)
        self.assertEqual(res_check.json()["code"], -20)

        res_check = self.user_check(username, username_1, 0)
        self.assertEqual(res_check.json()["code"], -2)


    def testSearchUser(self):
        username = random.randint(100_000_000_000, 999_999_999_999)
        password = random.randint(100_000_000_000, 999_999_999_999)

        username_1 = str(username) + "1"
        username_2 = str(username) + "12"
        username_3 = str(username) + "123"

        self.user_register(username, password)
        self.user_register(username_1, password)
        self.user_register(username_2, password)
        self.user_register(username_3, password)

        user_model = get_user_model()
        self.assertTrue(user_model.objects.filter(username=username_1).exists())

        # user_model = get_user_model()

        # user = user_model.objects.filter(username=username).first()
        # user_1 = user_model.objects.filter(username=username_1).first()
        # user_2 = user_model.objects.filter(username=username_2).first()
        # user_3 = user_model.objects.filter(username=username_3).first()

        res = self.user_search(username, username)
        self.assertEqual(res.json()["code"], 0)

        self.assertEqual(len(json.loads(res.json()["search_user_list"])),3)

