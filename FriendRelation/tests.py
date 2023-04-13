import json
import random

from django.test import TestCase
from django.contrib.auth import get_user_model

from django.contrib.auth.models import User
from UserManage.models import IMUser
from FriendRelation.models import Friend, FriendList


class FriendRelationTest(TestCase):

    def friend_group_create(self, username, token, fgroup_name):
        payload = {
            "username": username,
            "token": token,
            "fgroup_name": fgroup_name
        }
        return self.client.post("/friend/createfgroup", data=payload, content_type="application/json")

    def friend_list_get(self, username, token):
        payload = {
            "username": username,
            "token": token,
        }
        return self.client.post("/friend/getfriendlist", data=payload, content_type="application/json")

    def friend_to_group_add(self, username, token, friend_name, fgroup_name):
        payload = {
            "username": username,
            "token": token,
            "friend_name": friend_name,
            "fgroup_name": fgroup_name
        }
        return self.client.put("/friend/addfgroup", data=payload, content_type="application/json")

    def friend_delete(self, username, token, friend_name):
        payload = {
            "username": username,
            "token": token,
            "friend_name": friend_name
        }
        return self.client.delete("/friend/deletefriend", data=payload, content_type="application/json")

    def friend_group_delete(self, username, token, fgroup_name):
        payload = {
            "username": username,
            "token": token,
            "fgroup_name": fgroup_name
        }
        return self.client.delete("/friend/deletefgroup", data=payload, content_type="application/json")

    def test_fgroup_create(self):
        username = random.randint(100_000_000_000, 999_999_999_999)
        password = random.randint(100_000_000_000, 999_999_999_999)
        fgroup_name = random.randint(100_000_000_000, 999_999_999_999)

        self.user_register(username, password)
        res_login = self.user_login(username, password)

        token = res_login.json()["token"]
        res = self.friend_group_create(username, token, fgroup_name)
        self.assertJSONEqual(res.content, {"code": 0, "info": "CreateGroup Succeed"})
        self.assertEqual(res.json()["code"], 0)

        group_list = FriendList.objects.get(user_name=username).group_list

        self.assertTrue(str(fgroup_name) in group_list)


    def test_flist_get(self):
        username = random.randint(100_000_000_000, 999_999_999_999)
        password = random.randint(100_000_000_000, 999_999_999_999)
        fgroup_name = random.randint(100_000_000_000, 999_999_999_999)
        fname_base = random.randint(100_000_000_000, 999_000_000_000)
        self.user_register(username, password)
        res_login = self.user_login(username, password)
        token = res_login.json()["token"]
        cur_list = []

        self.friend_group_create(username, token, fgroup_name)

        cur_list.append({"groupname": "default", "userlist": []})

        cur_list.append({"groupname": fgroup_name, "userlist": []})
        # flist = FriendList.objects.filter(user_name=username, fgroup_name=fgroup_name).first()
        # 10个名字为数字的用户

        for i in range(10):
            cur_f = str(fname_base + 1)
            self.friend_to_group_add(username, token, cur_f, fgroup_name)
            for dics in cur_list:
                if dics["groupname"] == fgroup_name:
                    dics["userlist"].append(cur_f)

        res = self.friend_list_get(username, token)

        self.assertEqual(res.json()["code"], 0)

    def test_friend_to_group(self):
        username = random.randint(100_000_000_000, 999_999_999_999)
        password = random.randint(100_000_000_000, 999_999_999_999)
        fgroup_name = random.randint(100_000_000_000, 999_999_999_999)
        fname_base = random.randint(100_000_000_000, 999_000_000_000)
        self.user_register(username, password)
        res_login = self.user_login(username, password)
        token = res_login.json()["token"]
        self.friend_group_create(username, token, fgroup_name)
        res = self.friend_to_group_add(username, token, fname_base, fgroup_name)
        self.assertJSONEqual(res.content, {"code": 0, "info": "AddGroup Succeed"})

    def test_delete_friend(self):
        username = random.randint(100_000_000_000, 999_999_999_999)
        password = random.randint(100_000_000_000, 999_999_999_999)

        username_1 = username + 1

        self.user_register(username, password)
        self.user_register(username_1, password)

        token = self.user_login(username, password).json()["token"]

        friend_list = FriendList.objects.get(user_name=username)
        friend = Friend(user_name=username, friend_name=username_1, group_name=friend_list.group_list[0])
        friend.save()

        res = self.friend_delete(username, 0, username_1)
        self.assertEqual(res.json()["code"], -2)

        res = self.friend_delete(username, token, username - 1)
        self.assertEqual(res.json()["code"], -1)

        res = self.friend_delete(username, token, username_1)
        self.assertEqual(res.json()["code"], 0)

    def test_delete_fgroup(self):
        username = random.randint(100_000_000_000, 999_999_999_999)
        password = random.randint(100_000_000_000, 999_999_999_999)

        self.user_register(username, password)

        token = self.user_login(username, password).json()["token"]

        self.friend_group_create(username, token, "1")

        # token fail
        res = self.friend_group_delete(username, 0, "1")
        self.assertEqual(res.json()["code"], -2)

        #
        res = self.friend_group_delete(username, token, "2")
        self.assertEqual(res.json()["code"], -4)

        res = self.friend_group_delete(username, token, "1")
        self.assertEqual(res.json()["code"], 0)

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
            "my_username": my_username,
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

        self.assertEqual(len(res.json()["search_user_list"]), 3)
