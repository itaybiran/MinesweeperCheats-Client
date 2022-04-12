import json
import os
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
    REVEAL_BOARD_STARTING_X_POSITION, REVEAL_BOARD_STARTING_Y_POSITION, \
    CHANGE_BOARD_MIN_WIDTH, CHANGE_BOARD_DISTANCE_BETWEEN_BOARD_AND_WINDOW, \
    CHANGE_BOARD_DISTANCE_BETWEEN_BOARD_AND_LOWER_AREA, CHANGE_BOARD_UPPER_AREA_HEIGHT, CHANGE_BOARD_LOWER_AREA_HEIGHT, \
    CHANGE_BOARD_DISTANCE_BETWEEN_BOARD_AND_UPPER_AREA, RUNNING_FLAG, MIN_NUM_OF_BOMBS, CHANGE_BOARD_FIX_ALIGNMENT, \
    DEFAULT_PID, STATUS_CODE_OK, STATUS_CODE_BAD_REQUEST, IMG_INDEX
from utils import user_connection_manager, process_manager, board, calculates, pyqt_manager
from utils.board import calculate_board, add_button
from utils.memory import write_process_memory
from utils.message import MessageTypeEnum
from utils.user import User, set_user
from utils.winmine_exe import WinmineExe


class LoginScreen(QDialog):
    def __init__(self, user: User, window):
        super(LoginScreen, self).__init__()
        self.__user = user
        self.__window = window
        loadUi("gui/login.ui", self)
        user_connection_manager.disconnect(self.__user)
        self.__init_screen_objects()

    def __init_screen_objects(self):
        self.LoginButton.clicked.connect(lambda: self.__is_valid(self.__window.show_process_screen))
        self.NewUserButton.clicked.connect(self.__window.show_signup_screen)

    def __is_valid(self, show_process_screen):
        username = self.UsernameField.text()
        password = self.PasswordField.text()
        if username and password:
            response = requests.post(f"{SERVER_URL}/users/token", data={"username": username, "password": password})
            if response.status_code == STATUS_CODE_OK:
                token = response.json()["token_type"] + " " + response.json()["access_token"]
                set_user(token, self.__user)
                show_process_screen()
            elif response.status_code == STATUS_CODE_BAD_REQUEST:
                self.ErrorLabel.setText("Wrong username or password")
        else:
            self.ErrorLabel.setText("Please fill all fields")


class SignupScreen(QDialog):
    def __init__(self, user: User, window):
        super(SignupScreen, self).__init__()
        self.__user = user
        self.__window = window
        loadUi("gui/signup.ui", self)
        self.__init_screen_objects()

    def __init_screen_objects(self):
        self.OldUserButton.clicked.connect(self.__window.show_login_screen)
        self.SignupButton.clicked.connect(lambda: self.__register(self.__window.show_cheats_screen))

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


class AttachToProcessScreen(QDialog):
    def __init__(self, winmine: WinmineExe, user: User, window):
        super(AttachToProcessScreen, self).__init__()
        self.__winmine = winmine
        self.__window = window
        self.__user = user
        loadUi("gui/attach_to_process.ui", self)
        self.__init_screen_objects()
        threading.Thread(target=self.__update_boards_img_loop).start()

    def __init_screen_objects(self):
        self.CheatsButton.clicked.connect(self.__window.show_cheats_screen)
        self.MultiplayerButton.clicked.connect(self.__window.show_multiplayer_screen)
        self.LogoutButton.clicked.connect(self.__window.show_login_screen)
        self.ProcessList.itemDoubleClicked.connect(self.__attach_to_process)
        self.RefreshButton.clicked.connect(self.update)

    def __create_board_img_in_background(self, winmine):
        if winmine is not None:
            path_to_save = f"./img/boards/{winmine.get_pid()}.png"
            board.create_board(winmine.get_board(), path_to_save)

    def __update_boards_img_loop(self):
        while self.__window.is_running[0]:
            thread_list = []
            try:
                for index in range(self.ProcessList.count()):
                    winmine = self.ProcessList.item(index).data(WINMINE_INDEX)
                    thread_list.append(threading.Thread(target=self.__create_board_img_in_background, args=[winmine]))
                for thread in thread_list:
                    thread.start()
                for thread in thread_list:
                    thread.join()
                time.sleep(0.1)
                self.__update_process_list()
            except RuntimeError:
                pass

    def update(self) -> None:
        user_connection_manager.disconnect(self.__user)
        self.NameLabel.setText(self.__user.nickname)

    def __remove_closed_processes_from_list(self):
        pid_list_in_table = []
        for index in range(self.ProcessList.count()):
            pid_list_in_table.append(self.ProcessList.item(index).data(PID_INDEX))
        running_processes = process_manager.get_all_pids()
        for index, pid in enumerate(pid_list_in_table):
            if pid not in running_processes:
                self.ProcessList.takeItem(index)
                if pid == self.__winmine.get_pid():
                    self.__winmine.set_pid(DEFAULT_PID)

    def __add_new_running_processes_to_list(self):
        pid_list_in_table = []
        for index in range(self.ProcessList.count()):
            pid_list_in_table.append(self.ProcessList.item(index).data(PID_INDEX))
        running_processes = process_manager.get_available_pids()
        for pid in running_processes:
            if pid not in pid_list_in_table:
                winmine = WinmineExe(pid)
                img = f'<img src="img/boards/{pid}.png" size="{winmine.get_board_size()[1] * 8}" height="{winmine.get_board_size()[0] * 8}"/>'
                item = pyqt_manager.create_list_widget_item(repr(winmine), {WINMINE_INDEX: winmine, PID_INDEX: pid, IMG_INDEX: img})
                self.ProcessList.addItem(item)

    def __change_existing_running_processes_in_list(self):
        for index in range(self.ProcessList.count()):
            item = self.ProcessList.item(index)
            winmine = item.data(WINMINE_INDEX)
            pid = item.data(PID_INDEX)
            current_text = repr(item.data(WINMINE_INDEX))
            item.setData(3, f'<img src="img/boards/{pid}.png" size="{winmine.get_board_size()[1] * 8}" height="{winmine.get_board_size()[0] * 8}"/>')
            if item.text() != current_text:
                item.setText(current_text)

    def __remove_duplicates(self):
        pids_dict = {}
        for index in range(self.ProcessList.count()):
            if self.ProcessList.item(index).data(PID_INDEX) in pids_dict.keys():
                pids_dict[self.ProcessList.item(index).data(PID_INDEX)] += 1
            else:
                pids_dict[self.ProcessList.item(index).data(PID_INDEX)] = 1
        for pid in pids_dict.keys():
            if pids_dict[pid] > 1:
                for index in range(self.ProcessList.count()):
                    item: QListWidgetItem = self.ProcessList.item(index)
                    if item.data(PID_INDEX) == pid and item.icon() == QIcon(""):
                        self.ProcessList.takeItem(item)
                        break

    def __update_process_list(self):
        self.__remove_closed_processes_from_list()
        self.__add_new_running_processes_to_list()
        self.__change_existing_running_processes_in_list()
        process_manager.update_pids_file()
        self.__update_by_available_pid()
        self.__remove_duplicates()

    def __update_by_available_pid(self):
        pid_list_in_table = []
        for index in range(self.ProcessList.count()):
            pid_list_in_table.append(self.ProcessList.item(index).data(PID_INDEX))
        available_pids = process_manager.get_available_pids()
        for index, pid in enumerate(pid_list_in_table):
            if pid not in available_pids and pid != self.__winmine.get_pid():
                self.ProcessList.takeItem(index)

    def __attach_to_process(self, current_item):
        for index in range(self.ProcessList.count()):
            self.ProcessList.item(index).setIcon(QIcon(""))
        if current_item.data(PID_INDEX) != self.__winmine.get_pid():
            process_manager.change_pid_status(self.__winmine.get_pid())
            self.__winmine.set_pid(current_item.data(PID_INDEX))
            process_manager.change_pid_status(current_item.data(PID_INDEX))
        current_item.setIcon(QIcon("img/gui-icons/bomb-icon.png"))


class CheatsScreen(QDialog):
    def __init__(self, winmine: WinmineExe, user: User, window):
        super(CheatsScreen, self).__init__()
        self.__winmine = winmine
        self.__window = window
        self.__user = user
        loadUi("gui/cheats_widget.ui", self)
        self.__init_screen_objects()

    def __init_screen_objects(self):
        self.ChangeTimeButton.clicked.connect(self.__show_change_time_dialog)
        self.InitializeTimerButton.clicked.connect(self.__initialize_timer_button)
        self.ActiveTimerButton.toggled.connect(self.__active_timer_button)
        self.RevealBoardButton.clicked.connect(self.__show_reveal_board_dialog)
        self.ChangeBestTimesButton.clicked.connect(self.__show_change_best_times_dialog)
        self.ChangeBoardButton.clicked.connect(self.__show_change_board_dialog)
        self.MultiplayerButton.clicked.connect(self.__window.show_multiplayer_screen)
        self.ProcessButton.clicked.connect(self.__window.show_process_screen)
        self.LogoutButton.clicked.connect(self.__window.show_login_screen)
        self.ActiveTimerButton.setChecked(True)

    def update(self) -> None:
        if self.__winmine.get_pid() == DEFAULT_PID:
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
        self.ChangeTimeButton.setDisabled(is_disabled)
        self.InitializeTimerButton.setDisabled(is_disabled)
        self.ActiveTimerButton.setDisabled(is_disabled)
        self.RevealBoardButton.setDisabled(is_disabled)
        self.ChangeBoardButton.setDisabled(is_disabled)
        self.ChangeBestTimesButton.setDisabled(is_disabled)
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
        self.__init_screen_objects()

    def __init_screen_objects(self):
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
        self.bombs_counter = 0
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
        self.new_buttons_board = []
        self.__bombs_counter = 0
        loadUi("gui/change_board_dialog.ui", self)
        self.__init_screen_objects()

    def __init_screen_objects(self):
        self.__display_empty_board()
        self.__current_board_height = self.__winmine.get_board_size()[0]
        self.__current_board_width = self.__winmine.get_board_size()[1]
        self.ConfirmButton.clicked.connect(self.__change_board)
        self.RefreshButton.clicked.connect(self.__refresh)
        self.BombsBar.setValue(100)

    def __init_board(self, height):
        for i in range(height):
            self.new_buttons_board.append([])

    def __on_press(self, x, y):
        custom_button = self.new_buttons_board[x][y]
        max_bombs = calculates.calculate_max_bombs(len(self.new_buttons_board[0]), len(self.new_buttons_board))
        if custom_button.get_status():
            custom_button.setIcon(QIcon("img/board-icons/button.png"))
            self.__bombs_counter -= 1
            custom_button.change_status()
        elif self.__bombs_counter < max_bombs:
            custom_button.setIcon(QIcon("img/board-icons/bomb.png"))
            self.__bombs_counter += 1
            custom_button.change_status()
        self.__update_progress_bar()

    def __display_empty_board(self):
        for row in range(len(self.new_buttons_board)):
            for column in range(len(self.new_buttons_board[0])):
                self.new_buttons_board[row][column].hide()
        self.new_buttons_board = []
        height, width = self.__winmine.get_board_size()
        self.__init_board(height)
        self.setFixedHeight(CHANGE_BOARD_UPPER_AREA_HEIGHT + height * SQUARE_SIZE + CHANGE_BOARD_LOWER_AREA_HEIGHT)
        self.ChangeBoardWidget.setFixedHeight(
            CHANGE_BOARD_UPPER_AREA_HEIGHT + height * SQUARE_SIZE + CHANGE_BOARD_LOWER_AREA_HEIGHT)

        if width * SQUARE_SIZE < CHANGE_BOARD_MIN_WIDTH:
            self.setFixedWidth(CHANGE_BOARD_MIN_WIDTH)
            self.ChangeBoardWidget.setFixedWidth(CHANGE_BOARD_MIN_WIDTH)
        else:
            self.setFixedWidth(width * SQUARE_SIZE + CHANGE_BOARD_DISTANCE_BETWEEN_BOARD_AND_WINDOW)
            self.ChangeBoardWidget.setFixedWidth(width * SQUARE_SIZE + CHANGE_BOARD_DISTANCE_BETWEEN_BOARD_AND_WINDOW)

        y = int(CHANGE_BOARD_UPPER_AREA_HEIGHT + CHANGE_BOARD_DISTANCE_BETWEEN_BOARD_AND_UPPER_AREA)
        for row in range(height):
            x = int(self.geometry().width() / 2 - width * SQUARE_SIZE / 2) - CHANGE_BOARD_FIX_ALIGNMENT
            for column in range(width):
                custom_button = add_button(self, "button", x, y)
                custom_button.clicked.connect(partial(self.__on_press, x=row, y=column))
                self.new_buttons_board[row].append(custom_button)
                x += SQUARE_SIZE
            y += SQUARE_SIZE

        self.__current_board_width = width
        self.__current_board_height = height

        self.__move_screen_objects(y)

    def __move_screen_objects(self, y):
        self.ConfirmButton.move(int(self.width() / 2 - self.ConfirmButton.width() / 2),
                                y + CHANGE_BOARD_DISTANCE_BETWEEN_BOARD_AND_LOWER_AREA)
        self.ErrorLabel.move(int(self.width() / 2 - self.ErrorLabel.width() / 2),
                             y - 15 + CHANGE_BOARD_DISTANCE_BETWEEN_BOARD_AND_LOWER_AREA)
        self.Title.move(int(self.width() / 2 - self.Title.width() / 2), self.Title.pos().y())
        self.BombsBar.move(int(self.width() / 2 - self.BombsBar.width() / 2 + 20), self.BombsBar.pos().y())
        self.RefreshButton.move(int(self.width() - self.RefreshButton.width() - 10), self.RefreshButton.pos().y())

    def __change_board(self):
        if self.__current_board_height == self.__winmine.get_board_size()[0] or self.__current_board_width == \
                self.__winmine.get_board_size()[1]:
            if self.__winmine.is_in_middle_of_game():
                if self.__bombs_counter >= MIN_NUM_OF_BOMBS:
                    print(self.__get_new_board())
                    self.__winmine.restart_game(self.__get_new_board())
                    write_process_memory(self.__winmine.get_pid(), RUNNING_FLAG, 1, 1)
                    self.ErrorLabel.setText("")
                else:
                    self.ErrorLabel.setText("Please put at least 10 bombs")
            else:
                self.ErrorLabel.setText("Please click the smiley button")
        else:
            self.ErrorLabel.setText("Please click the refresh button")

    def __get_new_board(self):
        new_board = [[]]
        for row in range(len(self.new_buttons_board)):
            for button in self.new_buttons_board[row]:
                if button.get_status():
                    new_board[row].append("HIDDEN_BOMB")
                elif not button.get_status():
                    new_board[row].append("SAFE_PLACE")
            new_board.append([])
        new_board.pop()
        return new_board

    def __update_progress_bar(self):
        self.BombsBar.setValue(calculates.calculate_bombs_percentage(self.__bombs_counter,
                                                                     self.__current_board_width,
                                                                     self.__current_board_height))

    def __refresh(self):
        self.__bombs_counter = 0
        self.__update_progress_bar()
        self.__display_empty_board()


class ChangeBestTimesDialog(QDialog):
    def __init__(self, winmine: WinmineExe):
        super(ChangeBestTimesDialog, self).__init__()
        self.__winmine = winmine
        loadUi("gui/change_best_times_dialog.ui", self)
        self.__init_screen_objects()

    def __init_screen_objects(self):
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
        self.close()


class MultiplayerScreen(QDialog):
    def __init__(self, winmine: WinmineExe, user: User, window):
        super(MultiplayerScreen, self).__init__()
        self.__winmine = winmine
        self.__window = window
        self.__user = user
        self.__messages = []
        loadUi("gui/multiplayer.ui", self)
        self.__init_screen_objects()

    def __init_screen_objects(self):
        self.CheatsButton.clicked.connect(self.__window.show_cheats_screen)
        self.ProcessButton.clicked.connect(self.__window.show_process_screen)
        self.LogoutButton.clicked.connect(self.__window.show_login_screen)
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
