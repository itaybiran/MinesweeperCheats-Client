import json
import os
import shutil
import threading
import time
from functools import partial

import requests
import websocket
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog, QListWidgetItem
from PyQt5.uic import loadUi

from constants import SERVER_URL, INITIALIZE_TIME, MIN_TIME, MAX_TIME, PID_INDEX, WINMINE_INDEX, SQUARE_SIZE, \
    REVEAL_BOARD_STARTING_X_POSITION, REVEAL_BOARD_STARTING_Y_POSITION, \
    CHANGE_BOARD_MIN_WIDTH, CHANGE_BOARD_DISTANCE_BETWEEN_BOARD_AND_WINDOW, \
    CHANGE_BOARD_DISTANCE_BETWEEN_BOARD_AND_LOWER_AREA, CHANGE_BOARD_UPPER_AREA_HEIGHT, CHANGE_BOARD_LOWER_AREA_HEIGHT, \
    CHANGE_BOARD_DISTANCE_BETWEEN_BOARD_AND_UPPER_AREA, RUNNING_FLAG, MIN_NUM_OF_BOMBS, CHANGE_BOARD_FIX_ALIGNMENT, \
    DEFAULT_PID, STATUS_CODE_OK, STATUS_CODE_BAD_REQUEST, IMG_INDEX, NUMBER_OF_SECONDS_TO_COUNT_DOWN, \
    MODE_TO_NUMBER_OF_BOMBS, CUSTOM_MODE, WON, LOST, RANK_TO_ICON, EASY_MODE, INTIMIDATE_MODE, EXPERT_MODE, \
    WEBSOCKET_URL
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
        user_connection_manager.disconnect_http(self.__user)
        self.__init_screen_objects()

    def __init_screen_objects(self):
        self.LoginButton.clicked.connect(self.__is_valid)
        self.NewUserButton.clicked.connect(self.__window.show_signup_screen)

    def __is_valid(self):
        username = self.UsernameField.text()
        password = self.PasswordField.text()
        if username and password:
            response = requests.post(f"{SERVER_URL}/users/token", data={"username": username, "password": password})
            if response.status_code == STATUS_CODE_OK:
                token = response.json()["token_type"] + " " + response.json()["access_token"]
                set_user(token, self.__user)
                self.__window.init_reconnect_timer()
                self.__window.show_process_screen()
            elif response.status_code == STATUS_CODE_BAD_REQUEST:
                self.ErrorLabel.setText("Wrong username or password")
            elif response.status_code == 400:
                self.ErrorLabel.setText("User is already logged in")
        else:
            self.ErrorLabel.setText("Please fill all fields")

    def update(self):
        self.UsernameField.setText("")
        self.PasswordField.setText("")
        self.ErrorLabel.setText("")


class SignupScreen(QDialog):
    def __init__(self, user: User, window):
        super(SignupScreen, self).__init__()
        self.__user = user
        self.__window = window
        loadUi("gui/signup.ui", self)
        self.__init_screen_objects()

    def __init_screen_objects(self):
        self.OldUserButton.clicked.connect(self.__window.show_login_screen)
        self.SignupButton.clicked.connect(self.__register)

    def __register(self):
        username = self.UsernameField.text()
        password = self.PasswordField.text()
        confirm_password = self.ConfirmPasswordField.text()

        if username and password and confirm_password:
            if len(username) <= 10:
                if password == confirm_password:
                    response = requests.post(f"{SERVER_URL}/users/register",
                                             json={"nickname": username, "password": password})
                    if response.status_code == 200:
                        response = requests.post(f"{SERVER_URL}/users/token",
                                                 data={"username": username, "password": password})
                        if response.status_code == 200:
                            token = response.json()["token_type"] + " " + response.json()["access_token"]
                            set_user(token, self.__user)
                            self.__window.init_reconnect_timer()
                            self.__window.show_cheats_screen()
                        else:
                            self.ErrorLabel.setText("something went wrong")
                    elif response.status_code == 401:
                        self.ErrorLabel.setText("nickname is already taken")
                else:
                    self.ErrorLabel.setText("Passwords don't match")
            else:
                self.ErrorLabel.setText("Username cannot contain more than 10 characters")
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
            path_to_save = f"./img/boards_{self.__user.nickname}/{winmine.get_pid()}.png"
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
        if os.path.exists(f'img/boards_{self.__user.nickname}'):
            shutil.rmtree(f"img/boards_{self.__user.nickname}")

    def update(self) -> None:
        self.NameLabel.setText(self.__user.nickname)
        self.NameLabel.setIcon(QIcon(RANK_TO_ICON[self.__user.rank + 1]))
        if not os.path.exists(f'img/boards_{self.__user.nickname}'):
            os.mkdir(f"img/boards_{self.__user.nickname}")

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
                img = f'<img src="img/boards_{self.__user.nickname}/{pid}.png" size="{winmine.get_board_size()[1] * 8}" height="{winmine.get_board_size()[0] * 8}"/>'
                item = pyqt_manager.create_list_widget_item(repr(winmine),
                                                            {WINMINE_INDEX: winmine, PID_INDEX: pid, IMG_INDEX: img})
                self.ProcessList.addItem(item)

    def __change_existing_running_processes_in_list(self):
        for index in range(self.ProcessList.count()):
            item = self.ProcessList.item(index)
            winmine = item.data(WINMINE_INDEX)
            pid = item.data(PID_INDEX)
            current_text = repr(item.data(WINMINE_INDEX))
            item.setData(3,
                         f'<img src="img/boards_{self.__user.nickname}/{pid}.png" size="{winmine.get_board_size()[1] * 8}" height="{winmine.get_board_size()[0] * 8}"/>')
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
            self.__winmine.click_on_the_winmine()
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
        self.RevealBoardButton.clicked.connect(self.__show_reveal_board_dialog)
        self.ChangeBestTimesButton.clicked.connect(self.__show_change_best_times_dialog)
        self.ChangeBoardButton.clicked.connect(self.__show_change_board_dialog)
        self.MultiplayerButton.clicked.connect(self.__window.show_multiplayer_screen)
        self.ProcessButton.clicked.connect(self.__window.show_process_screen)
        self.LogoutButton.clicked.connect(self.__window.show_login_screen)
        self.StartTimerButton.clicked.connect(self.__start_timer)
        self.StopTimerButton.clicked.connect(self.__stop_timer)

    def set_buttons_status(self, is_disabled):
        self.ChangeTimeButton.setDisabled(is_disabled)
        self.InitializeTimerButton.setDisabled(is_disabled)
        self.StartTimerButton.setDisabled(is_disabled)
        self.StopTimerButton.setDisabled(is_disabled)
        self.RevealBoardButton.setDisabled(is_disabled)
        self.ChangeBoardButton.setDisabled(is_disabled)
        self.ChangeBestTimesButton.setDisabled(is_disabled)

    def update(self) -> None:
        if self.__winmine.get_pid() == DEFAULT_PID:
            self.ErrorLabel.setText("Cannot use cheats until a process is attached")
            self.set_buttons_status(True)
        else:
            self.ErrorLabel.setText("")
            self.set_buttons_status(False)
        self.NameLabel.setText(self.__user.nickname)
        self.NameLabel.setIcon(QIcon(RANK_TO_ICON[self.__user.rank + 1]))

    def __start_timer(self):
        self.update()
        self.__winmine.start_timer()

    def __stop_timer(self):
        self.update()
        self.__winmine.stop_timer()

    def __show_change_time_dialog(self):
        self.update()
        if self.__winmine.get_pid() != DEFAULT_PID:
            change_time_dialog = ChangeTimeDialog(self.__winmine)
            change_time_dialog.exec()

    def __show_reveal_board_dialog(self):
        self.update()
        if self.__winmine.get_pid() != DEFAULT_PID:
            reveal_board_dialog = RevealBoardDialog(self.__winmine)
            reveal_board_dialog.exec()

    def __show_change_best_times_dialog(self):
        self.update()
        if self.__winmine.get_pid() != DEFAULT_PID:
            change_best_times_dialog = ChangeBestTimesDialog(self.__winmine)
            change_best_times_dialog.exec()

    def __show_change_board_dialog(self):
        self.update()
        if self.__winmine.get_pid() != DEFAULT_PID:
            change_board_dialog = ChangeBoardDialog(self.__winmine)
            change_board_dialog.exec()

    def __initialize_timer_button(self):
        self.update()
        if self.__winmine.get_pid() != DEFAULT_PID:
            self.__winmine.change_timer(INITIALIZE_TIME)


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
        if self.__current_board_height == self.__winmine.get_board_size()[0] and self.__current_board_width == \
                self.__winmine.get_board_size()[1]:
            if self.__winmine.is_in_middle_of_game():
                if self.__bombs_counter >= MIN_NUM_OF_BOMBS:
                    self.__winmine.restart_game(self.__get_new_board(),
                                                calculates.calculate_number_of_bombs(self.__get_new_board()))
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
        self.__opponent_nickname = ""
        self.__opponent_rank = 0
        self.__number_of_safe_squares = 0
        self.__had_message = False
        loadUi("gui/multiplayer.ui", self)
        self.__init_screen_objects()

    def __init_screen_objects(self):
        self.CheatsButton.clicked.connect(self.__show_cheats_screen)
        self.ProcessButton.clicked.connect(self.__show_process_screen)
        self.LogoutButton.clicked.connect(self.__show_login_screen)
        self.ConnectButton.clicked.connect(self.__connect)
        self.SendButton.clicked.connect(self.__send_message)
        self.ConnectButton.clicked.connect(self.__connect)
        self.DisconnectButton.clicked.connect(self.__disconnect)
        self.__clicked_board = [[]]
        self.DisconnectButton.setVisible(False)
        self.ConnectButton.setVisible(True)

    def update(self) -> None:
        if self.__winmine.get_pid() == DEFAULT_PID:
            self.ErrorLabel.setText("Cannot use multiplayer until a process is attached")
            self.set_buttons_status(True)
        else:
            self.ErrorLabel.setText("")
            self.set_buttons_status(False)
        self.__had_message = False
        self.WinLabel.setVisible(False)
        self.LoseLabel.setVisible(False)
        self.ConnectButton.setVisible(True)
        self.DisconnectButton.setVisible(False)
        self.ExpertOpponentBoard.setVisible(False)
        self.EasyOpponentBoard.setVisible(False)
        self.IntermidiateOpponentBoard.setVisible(False)
        self.NameLabel.setText(self.__user.nickname)
        self.NameLabel.setIcon(QIcon(RANK_TO_ICON[self.__user.rank + 1]))
        self.ConnectingLabel.setText("")
        self.OpponentLabel.setText("")
        self.OpponentLabel.setIcon(QIcon(""))
        self.XpLabel.setText("")
        self.MessagesTable.clear()

    def set_buttons_status(self, is_disabled):
        self.ConnectButton.setDisabled(is_disabled)
        self.DisconnectButton.setDisabled(is_disabled)
        self.SendButton.setDisabled(is_disabled)

    def __handle_received_message(self, message):
        message = json.loads(json.loads(message))
        if message["type"] == MessageTypeEnum.chat_message:
            item = QListWidgetItem(message["data"])
            item.setTextAlignment(Qt.AlignRight)
            self.MessagesTable.addItem(item)
            self.MessagesTable.scrollToBottom()
        elif message["type"] == MessageTypeEnum.opponent_data:
            self.__opponent_nickname = message["data"]["nickname"]
            self.__opponent_rank = int(message["data"]["rank"]) + 1
            self.OpponentLabel.setText(self.__opponent_nickname)
            self.OpponentLabel.setIcon(QIcon(RANK_TO_ICON[self.__opponent_rank]))
            threading.Thread(target=self.__update_game_points).start()
        elif message["type"] == MessageTypeEnum.board:
            self.__display_opponent_clicked_board(json.loads(message["data"]))
            self.__clicked_board = json.loads(message["data"])
        elif message["type"] == MessageTypeEnum.init_board:
            self.__initialize_multiplayer_game(message["data"])
            threading.Thread(target=self.__is_loser_or_winner).start()
        elif message["type"] == MessageTypeEnum.win_or_lose:
            self.__display_game_result(message["data"])
            self.send_new_xp(message["data"])
        elif message["type"] == MessageTypeEnum.new_xp:
            if -(self.__user.xp - int(message["data"]["xp"])) >= 0:
                self.XpLabel.setText(f'(+{-(self.__user.xp - int(message["data"]["xp"]))}xp)')
            else:
                self.XpLabel.setText(f'({-(self.__user.xp - int(message["data"]["xp"]))}xp)')
            self.__user.xp = int(message["data"]["xp"])
            self.__user.rank = int(message["data"]["rank"])
            self.OpponentLabel.setText(self.__opponent_nickname)
            self.OpponentLabel.setIcon(QIcon(RANK_TO_ICON[self.__opponent_rank]))
            user_connection_manager.disconnect_ws(self.__user)

    def __display_game_result(self, winner_or_loser):
        if winner_or_loser == str(WON):
            self.WinLabel.setVisible(True)
            self.LoseLabel.setVisible(False)
        elif winner_or_loser == str(LOST):
            self.WinLabel.setVisible(False)
            self.LoseLabel.setVisible(True)

    def send_new_xp(self, winner_or_loser):
        clicked_board = self.__winmine.get_clicked_squares()[0]
        current_time = self.__winmine.get_timer()
        if winner_or_loser == str(WON):
            self.__send_message_with_protocol(
                str(self.__user.xp + calculates.calculate_game_point_win(clicked_board, current_time)), "new_xp")
        elif winner_or_loser == str(LOST):
            self.__send_message_with_protocol(
                str(self.__user.xp + calculates.calculate_game_point_lose(clicked_board, current_time)), "new_xp")

    def __initialize_multiplayer_game(self, board):
        self.__winmine.restart_game(board, MODE_TO_NUMBER_OF_BOMBS[self.__winmine.get_mode()])
        self.DisconnectButton.setDisabled(True)
        self.__winmine.count_backward(NUMBER_OF_SECONDS_TO_COUNT_DOWN)
        self.DisconnectButton.setDisabled(False)
        self.__winmine.start_timer()

    def __send_message_with_protocol(self, data: str, message_type: str):
        self.__user.ws.send(json.dumps({"data": data, "type": message_type}))

    def __send_message(self):
        if self.__user.ws != "" and self.__user.ws.keep_running and self.__had_message:
            message = self.ChatField.text()
            if message != "":
                self.__send_message_with_protocol(message, "chat_message")
                self.ChatField.setText("")
                item = QListWidgetItem(message)
                item.setTextAlignment(Qt.AlignLeft)
                item.setForeground(Qt.yellow)
                self.MessagesTable.addItem(item)
                self.MessagesTable.scrollToBottom()
        else:
            self.ErrorLabel.setText("Find an opponent first")

    def __check_if_mode_changed(self):
        self.__current_mode = self.__winmine.get_mode()
        while self.__user.ws.keep_running:
            if self.__current_mode != self.__winmine.get_mode() and not self.__had_message:
                self.__disconnect()

    def __update_game_points(self):
        self.ConnectingLabel.setText("")
        self.__current_mode = self.__winmine.get_mode()
        while self.__user.ws.keep_running:
            data = self.__winmine.get_clicked_squares()
            self.__send_message_with_protocol(str(data[0]), "board")
            time.sleep(1)

    def __display_opponent_clicked_board(self, clicked_board):
        board.create_clicked_board(clicked_board, f"./img/boards_{self.__user.nickname}/opponent_board.png")
        if self.__winmine.get_mode() == EASY_MODE:
            self.EasyOpponentBoard.setIcon(QIcon(f"./img/boards_{self.__user.nickname}/opponent_board.png"))
            self.EasyOpponentBoard.setIconSize(QSize(150, 150))
            self.EasyOpponentBoard.setVisible(True)
            self.IntermidiateOpponentBoard.setVisible(False)
            self.ExpertOpponentBoard.setVisible(False)
        elif self.__winmine.get_mode() == INTIMIDATE_MODE:
            self.IntermidiateOpponentBoard.setIcon(QIcon(f"./img/boards_{self.__user.nickname}/opponent_board.png"))
            self.IntermidiateOpponentBoard.setIconSize(QSize(200, 200))
            self.IntermidiateOpponentBoard.setVisible(True)
            self.EasyOpponentBoard.setVisible(False)
            self.ExpertOpponentBoard.setVisible(False)
        elif self.__winmine.get_mode() == EXPERT_MODE:
            self.ExpertOpponentBoard.setIcon(QIcon(f"./img/boards_{self.__user.nickname}/opponent_board.png"))
            self.ExpertOpponentBoard.setIconSize(QSize(300, 160))
            self.ExpertOpponentBoard.setVisible(True)
            self.EasyOpponentBoard.setVisible(False)
            self.IntermidiateOpponentBoard.setVisible(False)

    def __is_loser_or_winner(self):
        while self.__user.ws.keep_running:
            if not self.__winmine.is_time_running():
                if not self.__winmine.is_in_middle_of_game():
                    if self.__did_player_win():
                        self.__send_message_with_protocol(str(WON), "win_or_lose")
                    else:
                        self.__send_message_with_protocol(str(LOST), "win_or_lose")
                else:
                    self.__send_message_with_protocol(str(LOST), "win_or_lose")
            time.sleep(0.1)

    def __did_player_win(self):
        current_board = self.__winmine.get_board()
        number_of_bombs = MODE_TO_NUMBER_OF_BOMBS[self.__winmine.get_mode()]
        for row in range(len(current_board)):
            for column in range(len(current_board[0])):
                if current_board[row][column] == "RIGHT_FLAG":
                    number_of_bombs -= 1
        return number_of_bombs == 0

    def __on_message(self, ws, message):
        self.__had_message = True
        self.__handle_received_message(message)

    def __connect(self):
        if self.__winmine.get_pid() != DEFAULT_PID:
            self.set_buttons_status(False)
            if self.__winmine.get_mode() != CUSTOM_MODE:
                if self.__winmine.is_in_middle_of_game():
                    self.__number_of_safe_squares = calculates.calculate_number_of_safe_squares(
                        self.__winmine.get_board())
                    if self.__user.ws == "" or not self.__user.ws.keep_running:
                        self.ErrorLabel.setText("")
                        self.update()
                        self.ConnectButton.setVisible(False)
                        self.DisconnectButton.setVisible(True)
                        self.ConnectingLabel.setText("Connecting...")
                        self.__user.ws = websocket.WebSocketApp(
                            f"{WEBSOCKET_URL}/ws?nickname={self.__user.nickname}&rank={self.__user.rank}&difficulty={self.__winmine.get_mode()}",
                            header={"Authorization": self.__user.token}, on_message=self.__on_message)
                        threading.Thread(target=self.__user.ws.run_forever).start()
                        threading.Thread(target=self.__check_if_mode_changed).start()
                else:
                    self.ErrorLabel.setText("Please click the smiley button")
            else:
                self.ErrorLabel.setText("Please Choose Different Mode")
        else:
            self.ErrorLabel.setText("Cannot use multiplayer until a process is attached")
            self.set_buttons_status(True)

    def __disconnect(self):
        if not self.__had_message:
            user_connection_manager.disconnect_ws(self.__user)
        if self.__user.ws != "" and self.__user.ws.keep_running:
            self.__send_message_with_protocol(str(LOST), "win_or_lose")
        self.update()
        if self.__user.ws != "" and self.__user.ws.keep_running:
            self.__display_opponent_clicked_board(self.__clicked_board)

    def __show_cheats_screen(self):
        self.__disconnect()
        self.__window.show_cheats_screen()

    def __show_process_screen(self):
        self.__disconnect()
        self.__window.show_process_screen()

    def __show_login_screen(self):
        self.__disconnect()
        self.__window.show_login_screen()


class DisconnectDialog(QDialog):
    def __init__(self, user: User, window):
        super(DisconnectDialog, self).__init__()
        self.__window = window
        self.__user = user
        loadUi("gui/disconnect_dialog.ui", self)
        self.ReconnectButton.clicked.connect(self.__is_valid)

    def __is_valid(self):
        user_connection_manager.disconnect_http(self.__user)
        password = self.PasswordField.text()
        if password:
            response = requests.post(f"{SERVER_URL}/users/token",
                                     data={"username": self.__user.nickname, "password": password})
            if response.status_code == STATUS_CODE_OK:
                token = response.json()["token_type"] + " " + response.json()["access_token"]
                set_user(token, self.__user)
                self.__window.init_reconnect_timer()
                self.__window.return_from_reconnect_screen()
            elif response.status_code == STATUS_CODE_BAD_REQUEST:
                self.ErrorLabel.setText("Wrong password")
            elif response.status_code == 400:
                self.ErrorLabel.setText("User is already logged in")
        else:
            self.ErrorLabel.setText("Please fill all fields")
