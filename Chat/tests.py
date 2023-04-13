import json
from django.contrib.auth import get_user_model

from django.contrib.auth.models import User
from UserManage.models import IMUser
from django.test import TestCase

from channels.testing import ChannelsLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait


class ChatTest(ChannelsLiveServerTestCase):
    pass
