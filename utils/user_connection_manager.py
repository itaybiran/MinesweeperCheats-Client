import requests
from constants import SERVER_URL
from utils.user import User


def disconnect_ws(user: User) -> None:
    if user.ws != "" and user.ws.keep_running:
        user.ws.close()
    requests.post(f"{SERVER_URL}/disconnect-ws", headers={"Authorization": user.token}).json()


def disconnect_http(user: User) -> None:
    requests.post(f"{SERVER_URL}/disconnect-http", headers={"Authorization": user.token}).json()
