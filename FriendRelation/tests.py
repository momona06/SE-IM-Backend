import json
import random

from django.test import TestCase
from django.contrib.auth import get_user_model

from django.contrib.auth.models import User
from UserManage.models import IMUser
from FriendRelation.models import Friend, FriendList

USERNAME = "test00"
PASSWORD = "123456"

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


    def user_cancel(self, username, input_password):
        payload = {
            "username": username,
            "input_password": input_password
        }
        return self.client.delete("/user/cancel", data=payload, content_type="application/json")

    def test_fgroup_create(self):
        fgroup_name = "111"

        self.user_cancel(USERNAME,PASSWORD)
        self.user_register(USERNAME, PASSWORD)
        res_login = self.user_login(USERNAME, PASSWORD)

        token = res_login.json()["token"]
        res = self.friend_group_create(USERNAME, token, fgroup_name)
        self.assertJSONEqual(res.content, {"code": 0, "info": "CreateGroup Succeed"})
        self.assertEqual(res.json()["code"], 0)

        group_list = FriendList.objects.get(user_name=USERNAME).group_list

        self.assertTrue(str(fgroup_name) in group_list)


    def test_flist_get(self):
        fgroup_name = "1111"
        fname_base = 999999

        self.user_cancel(USERNAME,PASSWORD)
        self.user_register(USERNAME, PASSWORD)
        res_login = self.user_login(USERNAME, PASSWORD)
        token = res_login.json()["token"]
        cur_list = []

        self.friend_group_create(USERNAME, token, fgroup_name)

        cur_list.append({"groupname": "default", "userlist": []})

        cur_list.append({"groupname": fgroup_name, "userlist": []})
        # flist = FriendList.objects.filter(user_name=username, fgroup_name=fgroup_name).first()
        # 10个名字为数字的用户

        for i in range(10):
            cur_f = str(fname_base + 1)
            self.friend_to_group_add(USERNAME, token, cur_f, fgroup_name)
            for dics in cur_list:
                if dics["groupname"] == fgroup_name:
                    dics["userlist"].append(cur_f)

        res = self.friend_list_get(USERNAME, token)

        self.assertEqual(res.json()["code"], 0)

    def test_friend_to_group(self):
        fgroup_name = "1111"
        fname_base = 9999999

        self.user_cancel(USERNAME,PASSWORD)
        self.user_register(USERNAME, PASSWORD)
        res_login = self.user_login(USERNAME, PASSWORD)
        token = res_login.json()["token"]
        self.friend_group_create(USERNAME, token, fgroup_name)
        res = self.friend_to_group_add(USERNAME, token, fname_base, fgroup_name)
        self.assertJSONEqual(res.content, {"code": 0, "info": "AddGroup Succeed"})

    def test_delete_friend(self):
        username_1 = USERNAME + str(1)

        self.user_cancel(USERNAME,PASSWORD)
        self.user_cancel(username_1,PASSWORD)
        self.user_register(USERNAME, PASSWORD)
        self.user_register(username_1, PASSWORD)

        token = self.user_login(USERNAME, PASSWORD).json()["token"]

        friend_list1 = FriendList.objects.get(user_name=USERNAME)
        friend1 = Friend(user_name=USERNAME, friend_name=username_1, group_name=friend_list1.group_list[0])
        friend1.save()
        friend_list2 = FriendList.objects.get(user_name=username_1)
        friend2 = Friend(user_name=username_1, friend_name=USERNAME, group_name=friend_list2.group_list[0])
        friend2.save()

        res = self.friend_delete(USERNAME, 0, username_1)
        self.assertEqual(res.json()["code"], -2)

        res = self.friend_delete(USERNAME, token, USERNAME + "2")
        self.assertEqual(res.json()["code"], -1)

        res = self.friend_delete(USERNAME, token, username_1)
        self.assertEqual(res.json()["code"], 0)

    def test_delete_fgroup(self):
        self.user_cancel(USERNAME,PASSWORD)
        self.user_register(USERNAME, PASSWORD)

        token = self.user_login(USERNAME, PASSWORD).json()["token"]

        self.friend_group_create(USERNAME, token, "1")

        # token fail
        res = self.friend_group_delete(USERNAME, 0, "1")
        self.assertEqual(res.json()["code"], -2)

        #
        res = self.friend_group_delete(USERNAME, token, "2")
        self.assertEqual(res.json()["code"], -4)

        res = self.friend_group_delete(USERNAME, token, "1")
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
        username_1 = USERNAME

        self.user_cancel(USERNAME,PASSWORD)
        self.user_register(USERNAME, PASSWORD)
        res_login = self.user_login(USERNAME, PASSWORD)

        token = res_login.json()["token"]

        res_check = self.user_check(USERNAME, username_1, token)
        self.assertEqual(res_check.json()["code"], -4)

        username_1 = USERNAME + "11"

        self.user_register(username_1, PASSWORD)
        user_model = get_user_model()
        self.assertTrue(user_model.objects.filter(username=username_1).exists())

        res_check = self.user_check(USERNAME, username_1, token)
        self.assertEqual(res_check.json()["code"], 0)

        res_check = self.user_check(USERNAME + "987", username_1, token)
        self.assertEqual(res_check.json()["code"], -3)

        res_check = self.user_check(USERNAME, username_1 + "987", token)
        self.assertEqual(res_check.json()["code"], -20)

        res_check = self.user_check(USERNAME, username_1, 0)
        self.assertEqual(res_check.json()["code"], -2)

    def testSearchUser(self):
        username_1 = USERNAME + "1"
        username_2 = USERNAME + "12"
        username_3 = USERNAME + "123"

        self.user_cancel(USERNAME,PASSWORD)
        self.user_register(USERNAME, PASSWORD)
        self.user_register(username_1, PASSWORD)
        self.user_register(username_2, PASSWORD)
        self.user_register(username_3, PASSWORD)

        user_model = get_user_model()
        self.assertTrue(user_model.objects.filter(username=username_1).exists())

        # user_model = get_user_model()

        # user = user_model.objects.filter(username=username).first()
        # user_1 = user_model.objects.filter(username=username_1).first()
        # user_2 = user_model.objects.filter(username=username_2).first()
        # user_3 = user_model.objects.filter(username=username_3).first()

        res = self.user_search(USERNAME, USERNAME)
        self.assertEqual(res.json()["code"], 0)

        self.assertEqual(len(res.json()["search_user_list"]), 3)
