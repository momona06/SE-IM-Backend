from django.test import TestCase
from UserManage.models import IMUser
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
import json
import random

class UserManageTest(TestCase):
    def userRegister(self, username, password):
        payload = {
            "username": username,
            "password": password
        }
        return self.client.post("/user/register", data=payload, content_type="application/json")

    def userLogin(self, username, password, email=""):
        payload = {
            "username": username,
            "password": password,
            "email": email
        }
        return self.client.post("/user/login", data=payload, content_type="application/json")

    def userLogout(self, username, token):
        payload = {
            "username": username,
            "token": token
        }
        return self.client.delete("/user/logout", data=payload, content_type="application/json")

    def userCancel(self, username, input_password):
        payload = {
            "username": username,
            "input_password": input_password
        }
        return self.client.delete("/user/cancel", data=payload, content_type="application/json")

    def userRevise(self, revise_field, revise_content, username, input_password, token):
        payload = {
            "revise_field": revise_field,
            "revise_content": revise_content,
            "username": username,
            "input_password": input_password,
            "token": token
        }
        return self.client.put("/user/revise", data=payload, content_type="application/json")


    def testRegister(self):
        #username = secrets.token_hex(4)
        #password = secrets.token_hex(4)
        username = random.randint(100_000_000_000, 999_999_999_999)
        password = random.randint(100_000_000_000, 999_999_999_999)

        res = self.userRegister(username, password)

        self.assertJSONEqual(res.content, {"code": 0, "info": "Register Succeed"})
        self.assertEqual(res.json()["code"], 0)
        user_model = get_user_model()
        user = user_model.objects.filter(username=username).first()
        self.assertTrue(user_model.objects.filter(username=username).exists())
        self.assertTrue(IMUser.objects.filter(user=user).exists())

    def testLoginLogout(self):

        #username = secrets.token_hex(10)
        #password = secrets.token_hex(10)
        username = random.randint(100_000_000_000, 999_999_999_999)
        password = random.randint(100_000_000_000, 999_999_999_999)

        res_reg = self.userRegister(username, password)
        res_lin = self.userLogin(username, password)
        self.assertEqual(res_reg.json()["code"], 0)
        self.assertEqual(res_lin.json()["code"], 0)
        user_model = get_user_model()
        self.assertTrue(user_model.objects.filter(username=username).exists())

        user = user_model.objects.filter(username=username).first()
        im_user = IMUser.objects.filter(user=user).first()
        self.assertEqual(im_user.is_login, True)

        token = res_lin.json()["token"]
        res_lout = self.userLogout(username, token)
        im_user = IMUser.objects.filter(user=user).first()
        self.assertEqual(res_lout.json()["code"], 0)
        self.assertEqual(im_user.is_login, False)

    def testCancel(self):
        #username = secrets.token_hex(10)
        #password = secrets.token_hex(10)
        username = random.randint(100_000_000_000, 999_999_999_999)
        password = random.randint(100_000_000_000, 999_999_999_999)
        input_password = password

        res_reg = self.userRegister(username, password)
        res_lin = self.userLogin(username, password)
        self.assertEqual(res_lin.json()["code"], 0)

        user_model = get_user_model()
        self.assertTrue(user_model.objects.filter(username=username).exists())
        user = user_model.objects.filter(username=username).first()
        im_user = IMUser.objects.filter(user=user).first()

        self.assertEqual(im_user.is_login, True)

        res_cel = self.userCancel(username, input_password)
        self.assertFalse(user_model.objects.filter(username=username).exists())


    def testRevise(self):
        #username = secrets.token_hex(10)
        #password = secrets.token_hex(10)
        username = random.randint(100_000_000_000, 999_999_999_999)
        password = random.randint(100_000_000_000, 999_999_999_999)

        input_password = password
        res_reg = self.userRegister(username, password)
        res_lin = self.userLogin(username, password)
        self.assertEqual(res_reg.json()["code"], 0)
        self.assertEqual(res_lin.json()["code"], 0)

        user_model = get_user_model()
        self.assertTrue(user_model.objects.filter(username=username).exists())
        user = user_model.objects.filter(username=username).first()
        im_user = IMUser.objects.filter(user=user).first()

        token = res_lin.json()['token']

        # no email yet
        revise_field_list = ["username", "password"]
        revise_content_list = [random.randint(100_000_000_000, 999_999_999_999), random.randint(100_000_000_000, 999_999_999_999)]
        #for field, content in zip(revise_field_list, revise_content_list):
        res_rev = self.userRevise(revise_field_list[1], revise_content_list[1], username, input_password, token)
            #self.assertEqual(res_rev.json()["code"], 0)
            #self.assertEqual(res_rev.json()["info"],"dd")

        token = res_lin.json()["token"]
        res_lout = self.userLogout(username, token)
