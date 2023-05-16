import base64

# 编码
def encode(string):
    return base64.b64encode(string.encode())

# 解码
def decode(string):
    return base64.b64decode(string.encode())

async def async_encode(string):
    return base64.b64encode(string.encode())

async def async_decode(string):
    return base64.b64decode(string.encode())