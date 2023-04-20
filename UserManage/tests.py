from django.test import TestCase
from UserManage.models import IMUser
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from FriendRelation.models import FriendList
import json
import random

class UserManageTest(TestCase):
    def __init__(self):
        super().__init__()
        self.username = "test00"
        self.password = "123456"

        self.userCancel(self.username,self.password)


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

        self.userCancel(self.username,self.password)
        res = self.userRegister(self.username, self.password)

        self.assertJSONEqual(res.content, {"code": 0, "info": "Register Succeed"})
        self.assertEqual(res.json()["code"], 0)
        user_model = get_user_model()
        user = user_model.objects.filter(username=self.username).first()
        self.assertTrue(user_model.objects.filter(username=self.username).exists())
        self.assertTrue(IMUser.objects.filter(user=user).exists())

    def testLoginLogout(self):

        #username = secrets.token_hex(10)
        #password = secrets.token_hex(10)

        self.userCancel(self.username,self.password)
        res_reg = self.userRegister(self.username, self.password)
        res_lin = self.userLogin(self.username, self.password)
        self.assertEqual(res_reg.json()["code"], 0)
        self.assertEqual(res_lin.json()["code"], 0)
        user_model = get_user_model()
        self.assertTrue(user_model.objects.filter(username=self.username).exists())

        user = user_model.objects.filter(username=self.username).first()
        im_user = IMUser.objects.filter(user=user).first()

        token = res_lin.json()["token"]
        res_lout = self.userLogout(self.username, token)
        im_user = IMUser.objects.filter(user=user).first()
        self.assertEqual(res_lout.json()["code"], 0)

    def testCancel(self):
        #username = secrets.token_hex(10)
        #password = secrets.token_hex(10)
        self.userCancel(self.username,self.password)
        input_password = self.password

        res_reg = self.userRegister(self.username, self.password)
        res_lin = self.userLogin(self.username, self.password)
        self.assertEqual(res_lin.json()["code"], 0)

        user_model = get_user_model()
        self.assertTrue(user_model.objects.filter(username=self.username).exists())
        user = user_model.objects.filter(username=self.username).first()
        im_user = IMUser.objects.filter(user=user).first()


        res_cel = self.userCancel(self.username, input_password)
        self.assertFalse(user_model.objects.filter(username=self.username).exists())


    def testRevise(self):
        #username = secrets.token_hex(10)
        #password = secrets.token_hex(10)

        input_password = self.password
        res_reg = self.userRegister(self.username, self.password)
        res_lin = self.userLogin(self.username, self.password)
        self.assertEqual(res_reg.json()["code"], 0)
        self.assertEqual(res_lin.json()["code"], 0)

        user_model = get_user_model()
        self.assertTrue(user_model.objects.filter(username=self.username).exists())
        user = user_model.objects.filter(username=self.username).first()
        im_user = IMUser.objects.filter(user=user).first()

        token = res_lin.json()['token']

        # no email yet
        revise_field_list = ["username", "password"]
        revise_content_list = ["test01", "1234567"]
        #for field, content in zip(revise_field_list, revise_content_list):
        res_rev = self.userRevise(revise_field_list[1], revise_content_list[1], self.username, input_password, token)
        self.assertEqual(res_rev.json()["code"], 0)
            #self.assertEqual(res_rev.json()["info"],"dd")

        self.userRevise(revise_field_list[1], input_password, self.username, revise_content_list[1], token)
        token = res_lin.json()["token"]
        res_lout = self.userLogout(self.username, token)
