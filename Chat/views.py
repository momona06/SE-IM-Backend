import json
import re
import random

from django.http import HttpRequest, HttpResponse, JsonResponse
from utils.utils_request import BAD_METHOD
from django.contrib.auth import authenticate, get_user_model

from django.contrib.auth.models import User
from UserManage.models import IMUser, TokenPoll, CreateIMUser