import threading

import requests
import websocket
from IPython.core.release import url
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog, QListWidgetItem, QTableWidgetItem, QTableWidget
from PyQt5.uic import loadUi

from constants import SERVER_URL, INITIALIZE_TIME, MIN_TIME, MAX_TIME, PID_INDEX
from utils import user_connection_manager, process_manager
from utils.board import calculate_board, add_button
from utils.user import User, set_user
from utils.winmine_exe import WinmineExe


class LoginScreen(QDialog):
    def __init__(self, user: User, window):
        super(LoginScreen, self).__init__()
        self.__user = user
        loadUi("gui/login.ui", self)
        self.LoginButton.clicked.connect(lambda: self.__is_valid(window.show_process_screen))
        self.NewUserButton.clicked.connect(window.show_signup_screen)

    def __is_valid(self, show_process_screen):
        username = self.UsernameField.text()
        password = self.PasswordField.text()
        if username and password:
            response = requests.post(f"{SERVER_URL}/users/token", data={"username": username, "password": password})
            if response.status_code == 200:
                token = response.json()["token_type"] + " " + response.json()["access_token"]
                set_user(token, self.__user)
                show_process_screen()
            elif response.status_code == 401:
                self.ErrorLabel.setText("Wrong username or password")
        else:
            self.ErrorLabel.setText("Please fill all fields")


class SignupScreen(QDialog):
    def __init__(self, user: User, window):
        super(SignupScreen, self).__init__()
        self.__user = user
        loadUi("gui/signup.ui", self)
        self.OldUserButton.clicked.connect(window.show_login_screen)
        self.SignupButton.clicked.connect(lambda: self.__register(window.show_cheats_screen))

    def __register(self, show_cheats_screen):
        username = self.UsernameField.text()
        password = self.PasswordField.text()
        confirm_password = self.ConfirmPasswordField.text()

        if username and password and confirm_password:
            if password == confirm_password:
                response = requests.post(f"{SERVER_URL}/users/register",
                                         json={"nickname": username, "password": password})
                if response.status_code == 200:
                    response = requests.post(f"{SERVER_URL}/users/token",
                                             data={"username": username, "password": password})
                    if response.status_code == 200:
                        token = response.json()["token_type"] + " " + response.json()["access_token"]
                        set_user(token, self.__user)
                        show_cheats_screen()
                    else:
                        self.ErrorLabel.setText("something went wrong")
                elif response.status_code == 401:
                    self.ErrorLabel.setText("nickname is already taken")
            else:
                self.ErrorLabel.setText("Passwords don't match")
        else:
            self.ErrorLabel.setText("Please fill all fields")


class MultiplayerScreen(QDialog):
    def __init__(self, winmine: WinmineExe, user: User, window):
        super(MultiplayerScreen, self).__init__()
        self.__winmine = winmine
        self.__user = user
        self.__messages = []
        loadUi("gui/multiplayer.ui", self)
        self.CheatsButton.clicked.connect(window.show_cheats_screen)
        self.ProcessButton.clicked.connect(window.show_process_screen)
        self.ConnectButton.clicked.connect(self.__connect)
        self.SendButton.clicked.connect(self.__send_message)
        self.NameLabel.setText(self.__user.nickname)

    def update(self) -> None:
        self.NameLabel.setText(self.__user.nickname)
        self.ConnectButton.setText("Connect")
        self.ConnectingLabel.setText("")
        self.OpponentNameLabel.setText("")
        self.MessagesTable.clear()
        self.__messages = []

    def __send_message(self):
        if self.__user.ws != "" and self.__user.ws.keep_running:
            message = self.ChatField.text()
            if message != "":
                self.__user.ws.send(message)
                self.ChatField.setText("")
                item = QListWidgetItem(message)
                item.setTextAlignment(Qt.AlignLeft)
                self.MessagesTable.addItem(item)
                self.MessagesTable.scrollToBottom()
        else:
            self.ErrorLabel.setText("find an opponent first")

    def __on_message(self, ws, message):
        self.__messages.append(message)
        if len(self.__messages) > 1:
            item = QListWidgetItem(message)
            item.setTextAlignment(Qt.AlignRight)
            self.MessagesTable.addItem(item)
            self.MessagesTable.scrollToBottom()
        else:
            self.ConnectingLabel.setText("")
            self.OpponentNameLabel.setText(message)
            self.MessagesTable.clear()

    def __connect(self):
        if self.__user.ws == "" or not self.__user.ws.keep_running:
            self.ErrorLabel.setText("")
            self.ConnectButton.setText("Disconnect")
            self.ConnectingLabel.setText("Connecting...")
            self.__user.ws = websocket.WebSocketApp(
                f"ws://127.0.0.1:8000/ws?nickname={self.__user.nickname}&rank={self.__user.rank}&difficulty=0",
                header={"Authorization": self.__user.token}, on_message=self.__on_message)
            self.thread = threading.Thread(target=self.__user.ws.run_forever)
            self.thread.start()
        elif self.ConnectButton.text() == "Disconnect":
            user_connection_manager.disconnect(self.__user)
            self.update()


class CheatsScreen(QDialog):
    def __init__(self, winmine: WinmineExe, user: User, window):
        super(CheatsScreen, self).__init__()
        self.__winmine = winmine
        self.__user = user
        loadUi("gui/cheats_widget.ui", self)
        self.ChangeTimeButton.clicked.connect(self.__show_change_time_dialog)
        self.InitializeTimerButton.clicked.connect(self.__initialize_timer_button)
        self.ActiveTimerButton.toggled.connect(self.__active_timer_button)
        self.RevealBoardButton.clicked.connect(self.__show_reveal_board_dialog)
        self.MultiplayerButton.clicked.connect(window.show_multiplayer_screen)
        self.ProcessButton.clicked.connect(window.show_process_screen)
        self.ActiveTimerButton.setChecked(True)

    def update(self) -> None:
        user_connection_manager.disconnect(self.__user)
        self.NameLabel.setText(self.__user.nickname)
        self.RankLabel.setText("Rank: " + str(self.__user.rank))
        self.XpLabel.setText("Xp: " + str(self.__user.xp))

    def __show_change_time_dialog(self):
        change_time_dialog = ChangeTimeDialog(self.__winmine)
        change_time_dialog.exec()

    def __show_reveal_board_dialog(self):
        reveal_board_dialog = RevealBoardDialog(self.__winmine)
        reveal_board_dialog.exec()

    def __initialize_timer_button(self):
        self.__winmine.change_timer(INITIALIZE_TIME)

    def __active_timer_button(self):
        if self.ActiveTimerButton.isChecked():
            self.__winmine.start_timer()
        else:
            self.__winmine.stop_timer()


class ChangeTimeDialog(QDialog):
    def __init__(self, winmine: WinmineExe):
        super(ChangeTimeDialog, self).__init__()
        self.__winmine = winmine
        loadUi("gui/change_time_dialog.ui", self)
        self.OkButton.clicked.connect(self.__change_time)

    def __change_time(self):
        new_time = self.ChangeTimeTextField.text()
        if new_time.isnumeric() and MIN_TIME <= int(new_time) <= MAX_TIME:
            self.__winmine.change_timer(int(new_time))
            self.close()
        else:
            self.ErrorLabel.setText("Not a valid input")


class RevealBoardDialog(QDialog):
    def __init__(self, winmine: WinmineExe):
        super(RevealBoardDialog, self).__init__()
        self.__winmine = winmine
        loadUi("gui/reveal_board_dialog.ui", self)
        self.__reveal_board()

    def __reveal_board(self):
        current_board = calculate_board(self.__winmine.get_board())
        x = 10
        y = 10
        for row in range(len(current_board)):
            x = 10
            for column in range(len(current_board[row])):
                add_button(self, current_board[row][column], x, y)
                x += 16
            y += 16
        self.setFixedHeight(y + 16)
        self.setFixedWidth(x + 16)


class AttachToProcessScreen(QDialog):
    def __init__(self, winmine: WinmineExe, user: User, window):
        super(AttachToProcessScreen, self).__init__()
        self.__winmine = winmine
        self.__user = user
        loadUi("gui/attach_to_process.ui", self)
        self.CheatsButton.clicked.connect(window.show_cheats_screen)
        self.MultiplayerButton.clicked.connect(window.show_multiplayer_screen)
        self.ProcessList.itemDoubleClicked.connect(self.attach_to_process)

    def update(self) -> None:
        user_connection_manager.disconnect(self.__user)
        self.NameLabel.setText(self.__user.nickname)
        process_manager.update_pids_file()
        pids = process_manager.get_available_pids()
        winmines = process_manager.get_winmines(pids)
        self.__init_process_table(winmines)

    def __init_process_table(self, winmines):
        self.ProcessList.clear()
        if self.__winmine.get_pid() != 0:
            item = QListWidgetItem(repr(self.__winmine))
            item.setData(PID_INDEX, self.__winmine.get_pid())
            item.setIcon(QIcon("img/bomb-icon.png"))
            item.setData(3, '<img src="img/bomb-icon.png" width="512"/>')
            self.ProcessList.addItem(item)
        for winmine in winmines:
            item = QListWidgetItem(repr(winmine))
            item.setData(PID_INDEX, winmine.get_pid())
            item.setData(3, '<img src="img/bomb-icon.png" width="512"/>')
            self.ProcessList.addItem(item)

    def __attach_to_process(self, item):
        if item.data(PID_INDEX) != self.__winmine.get_pid():
            process_manager.change_pid_status(self.__winmine.get_pid())
            self.__winmine.set_pid(item.data(PID_INDEX))
            process_manager.change_pid_status(item.data(PID_INDEX))
            self.update()
