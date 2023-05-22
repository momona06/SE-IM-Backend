from django.test import TestCase
from UserManage.models import IMUser
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from FriendRelation.models import FriendList
import json
import random

PASSWORD = "123456"
USERNAME = "test00"


class UserManageTest(TestCase):
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

    def user_logout(self, username, token):
        payload = {
            "username": username,
            "token": token
        }
        return self.client.delete("/user/logout", data=payload, content_type="application/json")

    def user_cancel(self, username, input_password):
        payload = {
            "username": username,
            "input_password": input_password
        }
        return self.client.delete("/user/cancel", data=payload, content_type="application/json")

    def user_revise(self, revise_field, revise_content, username, input_password, token):
        payload = {
            "revise_field": revise_field,
            "revise_content": revise_content,
            "username": username,
            "input_password": input_password,
            "token": token
        }
        return self.client.put("/user/revise", data=payload, content_type="application/json")

    def user_send_email(self, email):
        payload = {
            "email": email
        }
        return self.client.post("/user/send_email", data=payload, content_type="application/json")

    def user_bind_email(self, email, code, username):
        payload = {
            "email": email,
            "code": code,
            "username": username
        }
        return self.client.post("/user/email", data=payload, content_type="application/json")

    def test_register(self):
        # username = secrets.token_hex(4)
        # password = secrets.token_hex(4)

        self.user_cancel(USERNAME, PASSWORD)
        res = self.user_register(USERNAME, PASSWORD)

        self.assertJSONEqual(res.content, {"code": 0, "info": "Register Succeed"})
        self.assertEqual(res.json()["code"], 0)
        user_model = get_user_model()
        user = user_model.objects.filter(username=USERNAME).first()
        self.assertTrue(user_model.objects.filter(username=USERNAME).exists())
        self.assertTrue(IMUser.objects.filter(user=user).exists())

    def test_login_logout(self):
        # username = secrets.token_hex(10)
        # password = secrets.token_hex(10)

        self.user_cancel(USERNAME, PASSWORD)
        res_reg = self.user_register(USERNAME, PASSWORD)
        res_lin = self.user_login(USERNAME, PASSWORD)
        self.assertEqual(res_reg.json()["code"], 0)
        self.assertEqual(res_lin.json()["code"], 0)
        user_model = get_user_model()
        self.assertTrue(user_model.objects.filter(username=USERNAME).exists())

        user = user_model.objects.filter(username=USERNAME).first()
        im_user = IMUser.objects.filter(user=user).first()

        token = res_lin.json()["token"]
        res_lout = self.user_logout(USERNAME, token)
        im_user = IMUser.objects.filter(user=user).first()
        self.assertEqual(res_lout.json()["code"], 0)

    def test_cancel(self):
        # username = secrets.token_hex(10)
        # password = secrets.token_hex(10)
        self.user_cancel(USERNAME, PASSWORD)
        input_password = PASSWORD

        res_reg = self.user_register(USERNAME, PASSWORD)
        res_lin = self.user_login(USERNAME, PASSWORD)
        self.assertEqual(res_lin.json()["code"], 0)

        user_model = get_user_model()
        self.assertTrue(user_model.objects.filter(username=USERNAME).exists())
        user = user_model.objects.filter(username=USERNAME).first()
        im_user = IMUser.objects.filter(user=user).first()

        res_cel = self.user_cancel(USERNAME, input_password)
        self.assertFalse(user_model.objects.filter(username=USERNAME).exists())

    def test_revise(self):
        # username = secrets.token_hex(10)
        # password = secrets.token_hex(10)

        input_password = PASSWORD
        res_reg = self.user_register(USERNAME, PASSWORD)
        res_lin = self.user_login(USERNAME, PASSWORD)
        self.assertEqual(res_reg.json()["code"], 0)
        self.assertEqual(res_lin.json()["code"], 0)

        user_model = get_user_model()
        self.assertTrue(user_model.objects.filter(username=USERNAME).exists())
        user = user_model.objects.filter(username=USERNAME).first()
        im_user = IMUser.objects.filter(user=user).first()

        token = res_lin.json()['token']

        # no email yet
        revise_field_list = ["username", "password"]
        revise_content_list = ["test01", "1234567"]
        # for field, content in zip(revise_field_list, revise_content_list):
        res_rev = self.user_revise(revise_field_list[1], revise_content_list[1], USERNAME, input_password, token)
        self.assertEqual(res_rev.json()["code"], 0)
        # self.assertEqual(res_rev.json()["info"],"dd")

        self.user_revise(revise_field_list[1], input_password, USERNAME, revise_content_list[1], token)
        token = res_lin.json()["token"]
        res_lout = self.user_logout(USERNAME, token)

    def test_email(self):
        username = USERNAME
        password = PASSWORD
        self.user_register(username, password)
        email = "zhoujin@mails.tsinghua.edu.cn"
        res = self.user_send_email(email)
        # res = self.userBindEmail(email,res_sms_code,username)
        self.assertEqual(res.json()["code"], 0)
