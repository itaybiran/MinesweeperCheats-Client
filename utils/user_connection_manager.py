import requests
from constants import SERVER_URL
from utils.user import User


def disconnect(user: User) -> None:
    if user.ws and user.ws.keep_running:
        user.ws.close()
    requests.post(f"{SERVER_URL}/disconnect", headers={"Authorization": user.token}).json()
