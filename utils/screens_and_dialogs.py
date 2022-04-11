import json
import threading
import time
from functools import partial

import requests
import websocket
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog, QListWidgetItem
from PyQt5.uic import loadUi

from constants import SERVER_URL, INITIALIZE_TIME, MIN_TIME, MAX_TIME, PID_INDEX, WINMINE_INDEX, SQUARE_SIZE, \
    REVEAL_BOARD_STARTING_X_POSITION, REVEAL_BOARD_STARTING_Y_POSITION, CHANGE_BOARD_UPPER_BUTTONS_AREA_HEIGHT, \
    CHANGE_BOARD_LOWER_BUTTONS_AREA_HEIGHT, CHANGE_BOARD_MIN_WIDTH, CHANGE_BOARD_DISTANCE_BETWEEN_BOARD_AND_WINDOW, \
    CHANGE_BOARD_DISTANCE_BETWEEN_BOARD_AND_UPPER_BUTTONS, CHANGE_BOARD_DISTANCE_BETWEEN_BOARD_AND_LOWER_BUTTONS, \
    CHANGE_BOARD_DISTANCE_BETWEEN_WIDTH_AND_HEIGHT_FIELDS
from utils import user_connection_manager, process_manager, board
from utils.board import calculate_board, add_button
from utils.message import MessageTypeEnum
from utils.user import User, set_user
from utils.winmine_exe import WinmineExe


class LoginScreen(QDialog):
    def __init__(self, user: User, window):
        super(LoginScreen, self).__init__()
        self.__user = user
        loadUi("gui/login.ui", self)
        self.LoginButton.clicked.connect(lambda: self.__is_valid(window.show_process_screen))
        self.NewUserButton.clicked.connect(window.show_signup_screen)
        user_connection_manager.disconnect(self.__user)

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
        self.LogoutButton.clicked.connect(window.show_login_screen)
        self.ConnectButton.clicked.connect(self.__connect)
        self.SendButton.clicked.connect(self.__send_message)
        self.NameLabel.setText(self.__user.nickname)

    def update(self) -> None:
        if self.__winmine.get_pid() == 0:
            self.ErrorLabel.setText("Cannot use multiplayer until a process is attached")
            self.set_buttons_status(True)
        else:
            self.ErrorLabel.setText("")
            self.set_buttons_status(False)
        self.NameLabel.setText(self.__user.nickname)
        self.ConnectButton.setText("Connect")
        self.ConnectingLabel.setText("")
        self.OpponentNameLabel.setText("")
        self.MessagesTable.clear()

    def set_buttons_status(self, is_disabled):
        # self.ConnectButton.setDisabled(is_disabled)
        # self.SendButton.setDisabled(is_disabled)
        pass

    def __handle_received_message(self, message):
        message = json.loads(json.loads(message))
        if message["type"] == MessageTypeEnum.chat_message:
            item = QListWidgetItem(message["data"])
            item.setTextAlignment(Qt.AlignRight)
            self.MessagesTable.addItem(item)
            self.MessagesTable.scrollToBottom()
        elif message["type"] == MessageTypeEnum.opponent_data:
            self.OpponentNameLabel.setText(message["data"]["nickname"])
            self.OpponentRankLabel.setText(str(message["data"]["rank"]))

    def __send_message_with_protocol(self, data: str, message_type: str):
        self.__user.ws.send(json.dumps({"data": data, "type": message_type}))

    def __send_message(self):
        if self.__user.ws != "" and self.__user.ws.keep_running:
            message = self.ChatField.text()
            if message != "":
                self.__send_message_with_protocol(message, "chat_message")
                self.ChatField.setText("")
                item = QListWidgetItem(message)
                item.setTextAlignment(Qt.AlignLeft)
                self.MessagesTable.addItem(item)
                self.MessagesTable.scrollToBottom()
        else:
            self.ErrorLabel.setText("find an opponent first")

    def __on_message(self, ws, message):
        self.__handle_received_message(message)

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
        self.ChangeBestTimesButton.clicked.connect(self.__show_change_best_times_dialog)
        self.ChangeBoardButton.clicked.connect(self.__show_change_board_dialog)
        self.MultiplayerButton.clicked.connect(window.show_multiplayer_screen)
        self.ProcessButton.clicked.connect(window.show_process_screen)
        self.LogoutButton.clicked.connect(window.show_login_screen)
        self.ActiveTimerButton.setChecked(True)

    def update(self) -> None:
        if self.__winmine.get_pid() == 0:
            self.ErrorLabel.setText("Cannot use cheats until a process is attached")
            self.set_buttons_status(True)
        else:
            self.ErrorLabel.setText("")
            self.set_buttons_status(False)
        user_connection_manager.disconnect(self.__user)
        self.NameLabel.setText(self.__user.nickname)
        self.RankLabel.setText("Rank: " + str(self.__user.rank))
        self.XpLabel.setText("Xp: " + str(self.__user.xp))

    def set_buttons_status(self, is_disabled):
        # self.ChangeTimeButton.setDisabled(is_disabled)
        # self.InitializeTimerButton.setDisabled(is_disabled)
        # self.ActiveTimerButton.setDisabled(is_disabled)
        # self.RevealBoardButton.setDisabled(is_disabled)
        # self.ChangeBoardButton.setDisabled(is_disabled)
        # self.ChangeBestTimesButton.setDisabled(is_disabled)
        pass

    def __show_change_time_dialog(self):
        change_time_dialog = ChangeTimeDialog(self.__winmine)
        change_time_dialog.exec()

    def __show_reveal_board_dialog(self):
        reveal_board_dialog = RevealBoardDialog(self.__winmine)
        reveal_board_dialog.exec()

    def __show_change_best_times_dialog(self):
        change_best_times_dialog = ChangeBestTimesDialog(self.__winmine)
        change_best_times_dialog.exec()

    def __show_change_board_dialog(self):
        change_board_dialog = ChangeBoardDialog(self.__winmine)
        change_board_dialog.exec()

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
        x = REVEAL_BOARD_STARTING_X_POSITION
        y = REVEAL_BOARD_STARTING_Y_POSITION
        for row in range(len(current_board)):
            x = REVEAL_BOARD_STARTING_X_POSITION
            for column in range(len(current_board[row])):
                add_button(self, current_board[row][column], x, y)
                x += SQUARE_SIZE
            y += SQUARE_SIZE
        self.setFixedHeight(y + SQUARE_SIZE)
        self.setFixedWidth(x + SQUARE_SIZE)


class ChangeBoardDialog(QDialog):
    def __init__(self, winmine: WinmineExe):
        super(ChangeBoardDialog, self).__init__()
        self.__winmine = winmine
        self.new_board = []
        loadUi("gui/change_board_dialog.ui", self)
        self.HeightField.setText("9")
        self.WidthField.setText("9")
        self.__display_empty_board()
        self.OkButton.clicked.connect(self.__display_empty_board)

    def __init_board(self, height):
        for i in range(height):
            self.new_board.append([])

    def __on_press(self, x, y):
        custom_button = self.new_board[x][y]
        if custom_button.get_status():
            custom_button.setIcon(QIcon("img/button.png"))
        else:
            custom_button.setIcon(QIcon("img/bomb.png"))
        custom_button.change_status()

    def __display_empty_board(self):
        for row in range(len(self.new_board)):
            for column in range(len(self.new_board[0])):
                self.new_board[row][column].hide()
        self.new_board = []
        height = int(self.HeightField.text())
        width = int(self.WidthField.text())
        self.__init_board(height)
        self.setFixedHeight(CHANGE_BOARD_UPPER_BUTTONS_AREA_HEIGHT + height * SQUARE_SIZE + CHANGE_BOARD_LOWER_BUTTONS_AREA_HEIGHT)
        self.ChangeBoardWidget.setFixedHeight(CHANGE_BOARD_UPPER_BUTTONS_AREA_HEIGHT + height * SQUARE_SIZE + CHANGE_BOARD_LOWER_BUTTONS_AREA_HEIGHT)
        if width * SQUARE_SIZE < CHANGE_BOARD_MIN_WIDTH:
            self.setFixedWidth(CHANGE_BOARD_MIN_WIDTH)
            self.ChangeBoardWidget.setFixedWidth(CHANGE_BOARD_MIN_WIDTH)
        else:

            self.setFixedWidth(width * SQUARE_SIZE + CHANGE_BOARD_DISTANCE_BETWEEN_BOARD_AND_WINDOW)
            self.ChangeBoardWidget.setFixedWidth(width * SQUARE_SIZE + CHANGE_BOARD_DISTANCE_BETWEEN_BOARD_AND_WINDOW)
        x = int(self.width() / 2 - width * SQUARE_SIZE / 2)
        y = int(CHANGE_BOARD_UPPER_BUTTONS_AREA_HEIGHT + CHANGE_BOARD_DISTANCE_BETWEEN_BOARD_AND_UPPER_BUTTONS)
        for row in range(height):
            x = int(self.geometry().width() / 2 - width * SQUARE_SIZE / 2)
            for column in range(width):
                custom_button = add_button(self, "button", x, y)
                custom_button.clicked.connect(partial(self.__on_press, x=row, y=column))
                self.new_board[row].append(custom_button)
                x += SQUARE_SIZE
            y += SQUARE_SIZE
        self.ConfirmButton.move(int(self.width() / 2 - self.ConfirmButton.width() / 2), y + CHANGE_BOARD_DISTANCE_BETWEEN_BOARD_AND_LOWER_BUTTONS)
        self.Title.move(int(self.width() / 2 - self.Title.width() / 2), self.Title.pos().y())
        self.WidthField.move(int(self.width() / 2 - self.WidthField.width() - CHANGE_BOARD_DISTANCE_BETWEEN_WIDTH_AND_HEIGHT_FIELDS / 2), self.WidthField.pos().y())
        self.HeightField.move(int(self.width() / 2 + CHANGE_BOARD_DISTANCE_BETWEEN_WIDTH_AND_HEIGHT_FIELDS / 2), self.HeightField.pos().y())
        self.OkButton.move(int(self.width() / 2 - self.OkButton.width() / 2), self.OkButton.pos().y())


class ChangeBestTimesDialog(QDialog):
    def __init__(self, winmine: WinmineExe):
        super(ChangeBestTimesDialog, self).__init__()
        self.__winmine = winmine
        loadUi("gui/change_best_times_dialog.ui", self)
        self.OkButton.clicked.connect(self.__change_best_times)
        self.TimeSlider.setValue(0)
        self.__value_change()
        self.TimeSlider.valueChanged.connect(self.__value_change)

    def __value_change(self):
        txt = str(self.TimeSlider.value())
        self.DisplayTimeLabel.setText(txt)

    def __change_best_times(self):
        difficulty = self.DifficultyBox.currentText()
        name = self.NameTextField.text()
        new_time = self.TimeSlider.value()
        if name == "":
            name = "Anonymous"
        self.__winmine.set_best_times(difficulty, name, new_time)
        # self.__winmine.change_best_time(difficulty, name, new_time)
        self.close()


class AttachToProcessScreen(QDialog):
    def __init__(self, winmine: WinmineExe, user: User, window):
        super(AttachToProcessScreen, self).__init__()
        self.__winmine = winmine
        self.__user = user
        loadUi("gui/attach_to_process.ui", self)
        self.CheatsButton.clicked.connect(window.show_cheats_screen)
        self.MultiplayerButton.clicked.connect(window.show_multiplayer_screen)
        self.LogoutButton.clicked.connect(window.show_login_screen)
        self.ProcessList.itemDoubleClicked.connect(self.__attach_to_process)
        self.RefreshButton.clicked.connect(self.update)

    def __create_boards_img_in_background(self):
        thread_list = []
        try:
            for index in range(self.ProcessList.count()):
                winmine = self.ProcessList.item(index).data(WINMINE_INDEX)
                thread_list.append(threading.Thread(target=board.create_board, args=[winmine.get_board(), f"./img/boards/{winmine.get_pid()}.png"]))
            for thread in thread_list:
                thread.start()
            for thread in thread_list:
                thread.join()
            return True
        except Exception as e:
            print(e)
            return False

    def update_boards_img_loop(self):
        flag = self.__create_boards_img_in_background()
        while flag:
            flag = self.__create_boards_img_in_background()
            time.sleep(3)

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
            item.setData(3, f'<img src="img/boards/{item.data(PID_INDEX)}.png" size="{self.__winmine.get_board_size()[1]*8}" height="{self.__winmine.get_board_size()[0]*8}"/>')
            item.setData(WINMINE_INDEX, self.__winmine)
            self.ProcessList.addItem(item)
        for winmine in winmines:
            item = QListWidgetItem(repr(winmine))
            item.setData(PID_INDEX, winmine.get_pid())
            item.setData(3, f'<img src="img/boards/{item.data(PID_INDEX)}.png" width="{winmine.get_board_size()[1]*8}" height="{winmine.get_board_size()[0]*8}"/>')
            item.setData(WINMINE_INDEX, winmine)
            self.ProcessList.addItem(item)

    def __attach_to_process(self, item):
        if item.data(PID_INDEX) != self.__winmine.get_pid():
            process_manager.change_pid_status(self.__winmine.get_pid())
            self.__winmine.set_pid(item.data(PID_INDEX))
            process_manager.change_pid_status(item.data(PID_INDEX))
            self.update()
