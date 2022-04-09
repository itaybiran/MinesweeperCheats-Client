import requests
from constants import *


class User:
    def __init__(self, nickname="", rank=0, xp=0, token="", ws=""):
        self.nickname = nickname
        self.rank = rank
        self.xp = xp
        self.token = token
        self.ws = ws


def get_current_user_info(user_token):
    return requests.get(f"{SERVER_URL}/users/info", headers={"Authorization": user_token}).json()


def set_user(user_token, user: User):
    info = get_current_user_info(user_token)
    user.nickname = info["nickname"]
    user.rank = info["rank"]
    user.xp = info["xp"]
    user.token = user_token
