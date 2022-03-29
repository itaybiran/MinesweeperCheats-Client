import sys

from PyQt5.QtWidgets import QWidget, QApplication, QStackedWidget, QDialog
from PyQt5.uic import loadUi
from reserch import *
import requests

MAX_TIME = 999
MIN_TIME = 0
INITIALIZE_TIME = 0
SERVER_URL = "http://localhost:8000"


class Window(QDialog):
    def __init__(self, widget, winmine):
        super(Window, self).__init__()
        self.widget = widget
        self.winmine = winmine

    def init_window(self, width, height):
        self.widget.setFixedWidth(width)
        self.widget.setFixedHeight(height)
        self.widget.show()

    def show_cheats_screen(self):
        cheats_screen = CheatsScreen(self.widget, self.winmine)
        self.widget.addWidget(cheats_screen)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def show_signup_screen(self):
        signup_screen = SignupScreen(self.widget, self.winmine)
        self.widget.addWidget(signup_screen)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def show_login_screen(self):
        login_screen = LoginScreen(self.widget, self.winmine)
        self.widget.addWidget(login_screen)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)


class LoginScreen(Window):
    def __init__(self, widget, winmine):
        super(LoginScreen, self).__init__(widget, winmine)
        loadUi("gui/login.ui", self)
        self.LoginButton.clicked.connect(self.is_valid)
        self.NewUserButton.clicked.connect(self.show_signup_screen)

    def is_valid(self):
        username = self.UsernameField.text()
        password = self.PasswordField.text()
        if username and password:
            response = requests.post(f"{SERVER_URL}/users/token", data={"username": username, "password": password})
            if response.status_code == 200:
                self.show_cheats_screen()
            elif response.status_code == 401:
                self.ErrorLabel.setText("Wrong username or password")
        else:
            self.ErrorLabel.setText("Please fill all fields")


class SignupScreen(Window):
    def __init__(self, widget, winmine):
        super(SignupScreen, self).__init__(widget, winmine)
        loadUi("gui/signup.ui", self)
        self.OldUserButton.clicked.connect(super().show_login_screen)
        self.SignupButton.clicked.connect(self.register)

    def register(self):
        username = self.UsernameField.text()
        password = self.PasswordField.text()
        confirm_password = self.ConfirmPasswordField.text()
        if username and password and confirm_password:
            if password == confirm_password:
                response = requests.post(f"{SERVER_URL}/users/register",
                                         json={"nickname": username, "password": password})
                if response.status_code == 200:
                    self.show_cheats_screen()
                elif response.status_code == 401:
                    self.ErrorLabel.setText("nickname is already taken")
            else:
                self.ErrorLabel.setText("Passwords don't match")
        else:
            self.ErrorLabel.setText("Please fill all fields")


class CheatsScreen(Window):
    def __init__(self, widget, winmine):
        super(CheatsScreen, self).__init__(widget, winmine)
        loadUi("gui/cheats_widget.ui", self)
        self.ChangeTimeButton.clicked.connect(self.show_change_time_dialog)
        self.InitializeTimerButton.clicked.connect(self.initialize_timer_button)
        self.ActiveTimerButton.toggled.connect(self.active_timer_button)
        self.ActiveTimerButton.setChecked(True)

    def show_change_time_dialog(self):
        change_time_dialog = ChangeTimeDialog(self.winmine)
        change_time_dialog.exec()

    def initialize_timer_button(self):
        self.winmine.change_timer(INITIALIZE_TIME)

    def active_timer_button(self):
        if self.ActiveTimerButton.isChecked():
            self.winmine.start_timer()
        else:
            self.winmine.stop_timer()


class ChangeTimeDialog(QDialog):
    def __init__(self, winmine):
        self.winmine = winmine
        super(ChangeTimeDialog, self).__init__()
        loadUi("gui/change_time_dialog.ui", self)
        self.OkButton.clicked.connect(self.change_time)

    def change_time(self):
        new_time = self.ChangeTimeTextField.text()
        if new_time.isnumeric() and MIN_TIME <= int(new_time) <= MAX_TIME:
            self.winmine.change_timer(int(new_time))
            self.close()
        else:
            self.ErrorLabel.setText("Not a valid input")


def main():
    pid = get_process_pid("Winmine__XP.exe")[1]
    winmine = WinmineExe(pid)

    app = QApplication(sys.argv)
    widget = QStackedWidget()

    window = Window(widget, winmine)
    window.show_login_screen()
    window.init_window(700, 400)

    try:
        sys.exit(app.exec_())
    except:
        print("Exiting")
        sys.exit()


if __name__ == '__main__':
    main()
