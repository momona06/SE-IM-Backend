import base64

from asgiref.sync import sync_to_async


# 编码
def encode(string):
    return base64.b64encode(string.encode())

# 解码
def decode(string):
    return base64.b64decode(string.encode())

@sync_to_async
def async_encode(string):
    return base64.b64encode(string.encode())

@sync_to_async
def async_decode(string):
    return base64.b64decode(string.encode())