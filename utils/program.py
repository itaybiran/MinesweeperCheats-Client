import sys
import requests
from PyQt5.QtWidgets import QApplication
from constants import SERVER_URL
from utils import process_manager
from utils.user import User
from utils.window import Window
from utils.winmine_exe import WinmineExe


class Program:
    def __init__(self):
        self.__winmine: WinmineExe = WinmineExe()
        self.__user: User = User()
        self.__app = QApplication(sys.argv)
        self.__window = Window(self.__winmine, self.__user)

    def run(self):
        self.__window.show_login_screen()
        try:
            self.__app.exec_()
            self.__exit()
        except Exception as e:
            print(e)
            self.__exit()

    def __exit(self):
        process_manager.change_pid_status(self.__winmine.get_pid())
        if self.__user.ws and self.__user.ws.keep_running:
            self.__user.ws.close()
        requests.post(f"{SERVER_URL}/disconnect", headers={"Authorization": self.__user.token}).json()
        sys.exit()
