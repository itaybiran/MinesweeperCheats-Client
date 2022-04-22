import sys
from PyQt5.QtWidgets import QApplication
from utils import process_manager, user_connection_manager
from utils.user import User
from utils.window import Window
from utils.winmine_exe import WinmineExe


class Program:
    def __init__(self):
        self.__winmine: WinmineExe = WinmineExe()
        self.__user: User = User()
        self.__app = QApplication(sys.argv)
        self.__is_running = [True]
        self.__window = Window(self.__winmine, self.__user, self.__is_running)

    def run(self):
        self.__window.show_login_screen()
        try:
            self.__app.exec_()
            self.exit()
        except Exception as e:
            print(e)
            self.exit()

    def exit(self):
        self.__is_running[0] = False
        process_manager.change_pid_status(self.__winmine.get_pid())
        if self.__user.ws and self.__user.ws.keep_running:
            self.__user.ws.close()
        user_connection_manager.disconnect_ws(self.__user)
        user_connection_manager.disconnect_http(self.__user)
        self.__window.cancel_reconnect_timer()
        sys.exit()
