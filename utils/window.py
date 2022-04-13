import threading
import time

from PyQt5.QtWidgets import QStackedWidget
from constants import WIDTH, HEIGHT
from utils import user_connection_manager
from utils.screens_and_dialogs import LoginScreen, CheatsScreen, MultiplayerScreen, SignupScreen, AttachToProcessScreen
from utils.user import User
from utils.winmine_exe import WinmineExe


class Window:
    def __init__(self, winmine: WinmineExe, user: User, is_running):
        self.__widget = QStackedWidget()
        self.__winmine = winmine
        self.is_running = is_running
        self.__user = user
        self.__login_screen = LoginScreen(self.__user, self)
        self.__signup_screen = SignupScreen(self.__user, self)
        self.__cheats_screen = CheatsScreen(self.__winmine, self.__user, self)
        self.__multiplayer_screen = MultiplayerScreen(self.__winmine, self.__user, self)
        self.__process_screen = AttachToProcessScreen(self.__winmine, self.__user, self)
        self.__set_window_size(WIDTH, HEIGHT)
        self.__widget.show()

    def __set_window_size(self, width, height):
        self.__widget.setFixedWidth(width)
        self.__widget.setFixedHeight(height)

    def show_cheats_screen(self):
        self.__cheats_screen.update()
        self.__widget.addWidget(self.__cheats_screen)
        self.__widget.setCurrentIndex(self.__widget.currentIndex() + 1)

    def show_multiplayer_screen(self):
        self.__multiplayer_screen.update()
        self.__widget.addWidget(self.__multiplayer_screen)
        self.__widget.setCurrentIndex(self.__widget.currentIndex() + 1)

    def show_process_screen(self):
        self.__process_screen.update()
        self.__widget.addWidget(self.__process_screen)
        self.__widget.setCurrentIndex(self.__widget.currentIndex() + 1)

    def show_signup_screen(self):
        self.__widget.addWidget(self.__signup_screen)
        self.__widget.setCurrentIndex(self.__widget.currentIndex() + 1)

    def show_login_screen(self):
        user_connection_manager.disconnect_http(self.__user)
        self.__widget.addWidget(self.__login_screen)
        self.__widget.setCurrentIndex(self.__widget.currentIndex() + 1)
