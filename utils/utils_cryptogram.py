import base64

from asgiref.sync import sync_to_async


def encode(string):
    """
    编码
    """
    return base64.b64encode(string.encode()).decode("utf-8")


def decode(string):
    """
    解码
    """
    return base64.b64decode(string).decode("utf-8")


@sync_to_async
def async_encode(string):
    """
    编码
    """
    return base64.b64encode(string.encode()).decode("utf-8")


@sync_to_async
def async_decode(string):
    """
    解码
    """
    return base64.b64decode(string).decode("utf-8")