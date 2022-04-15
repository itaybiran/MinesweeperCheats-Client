import ctypes
import threading
import time
from winreg import *
import win32gui
import win32process
from win32con import SW_HIDE, SW_SHOW
from constants import *
from utils import calculates
from utils.memory import write_process_memory, read_process_memory
ConnectRegistry(None, HKEY_LOCAL_MACHINE)


class WinmineExe(object):
    def __init__(self, pid=0):
        self.__pid = pid

    def get_pid(self):
        return self.__pid

    def set_pid(self, pid):
        self.__pid = pid

    def change_timer(self, new_time):
        write_process_memory(self.__pid, SECONDS_COUNTER, new_time, 2)
        self.redraw_window()

    def get_timer(self):
        return read_process_memory(self.__pid, SECONDS_COUNTER, 1)

    def stop_timer(self):
        write_process_memory(self.__pid, TIMER_FLAG, 0, 1)

    def start_timer(self):
        write_process_memory(self.__pid, TIMER_FLAG, 1, 1)

    def is_time_running(self):
        return read_process_memory(self.__pid, TIMER_FLAG, 1)

    def get_board(self) -> list[list]:
        """A function that returns a matrix represents the board."""
        board = [[]]
        height, width = self.get_board_size()
        for row in range(height):
            for column in range(width):
                memory_address = BOARD_TOP_LEFT_CORNER + column + (row * TWO_LINES)
                current_block = read_process_memory(self.__pid, memory_address, 1)
                board[row].append(VALUE_TO_SYMBOL[current_block])
            board.append([])
        board.pop()  # pop the empty list
        return board

    def set_board(self, board):
        """A function that gets a board and sets the game to this board."""
        height = len(board)
        width = len(board[0])
        # Sets everything to unused area
        for memory_address in range(BOARD_BOUNDARY_TOP_LEFT_CORNER_ADDRESS, LAST_MEMORY_REPRESENTING_BOARD):
            write_process_memory(self.__pid, memory_address, UNUSED_AREA, 1)
        # Sets the top boundary
        for memory_address in range(BOARD_BOUNDARY_TOP_LEFT_CORNER_ADDRESS,
                                    BOARD_BOUNDARY_TOP_LEFT_CORNER_ADDRESS + width + 2):
            write_process_memory(self.__pid, memory_address, BOUNDARY, 1)
        # Sets the bottom boundary
        for memory_address in range(BOARD_BOUNDARY_TOP_LEFT_CORNER_ADDRESS + (height + 1) * TWO_LINES,
                                    BOARD_BOUNDARY_TOP_LEFT_CORNER_ADDRESS + (height + 1) * TWO_LINES + width + 2):
            write_process_memory(self.__pid, memory_address, BOUNDARY, 1)
        # Sets the body of the board
        for row in range(height):
            memory_address = BOARD_TOP_LEFT_CORNER + row * TWO_LINES - 1
            write_process_memory(self.__pid, memory_address, BOUNDARY, 1)
            for column in range(width):
                memory_address = BOARD_TOP_LEFT_CORNER + column + row * TWO_LINES
                write_process_memory(self.__pid, memory_address,
                                     list(VALUE_TO_SYMBOL.keys())[
                                         list(VALUE_TO_SYMBOL.values()).index(board[row][column])],
                                     1)
            memory_address = BOARD_TOP_LEFT_CORNER + width + row * TWO_LINES
            write_process_memory(self.__pid, memory_address, BOUNDARY, 1)

    def get_board_size(self):
        height = read_process_memory(self.__pid, BOARD_HEIGHT_ADDRESS, 1)
        width = read_process_memory(self.__pid, BOARD_WIDTH_ADDRESS, 1)
        return height, width

    def set_board_size(self, height, width):
        write_process_memory(self.__pid, BOARD_WIDTH_MENU_ADDRESS, height, 1)
        write_process_memory(self.__pid, BOARD_HEIGHT_MENU_ADDRESS, height, 1)
        write_process_memory(self.__pid, BOARD_HEIGHT_ADDRESS, height, 1)
        write_process_memory(self.__pid, BOARD_WIDTH_ADDRESS, width, 1)
        write_process_memory(self.__pid, PIXELS_TO_DRAW_HEIGHT_ADDRESS, height*SQUARE_SIZE + BAR_PIXELS_HEIGHT, 2)
        write_process_memory(self.__pid, PIXELS_TO_DRAW_WIDTH_ADDRESS, width*SQUARE_SIZE + BAR_PIXELS_WIDTH, 2)

    def write_to_winmine_registry(self, key, new_value):
        key_handle = OpenKey(HKEY_CURRENT_USER, WINMINE_REGISTRY_PATH, 0, KEY_ALL_ACCESS)
        SetValueEx(key_handle, key, 0, CONVERT_TYPE[str(type(new_value))], new_value)

    def change_best_time(self, difficulty, player_name, new_time):
        self.write_to_winmine_registry("Time" + str(MODE_TO_NUMBER[difficulty] + 1), new_time)
        self.write_to_winmine_registry("Name" + str(MODE_TO_NUMBER[difficulty] + 1), player_name[0: MAX_NAME_LENGTH])

    def get_mode(self):
        return read_process_memory(self.__pid, MODE_ADDRESS, 1)

    def set_mode(self, mode):
        write_process_memory(self.__pid, MODE_ADDRESS, mode, 1)

    def get_number_of_bombs(self):
        return read_process_memory(self.__pid, NUMBER_OF_BOMBS_ADDRESS, 1)

    def set_number_of_bombs(self, new_number_of_bombs):
        # write_process_memory(self.__pid, 0x010056A4, new_number_of_bombs, 1)
        write_process_memory(self.__pid, NUMBER_OF_BOMBS_ADDRESS, new_number_of_bombs, 1)
        write_process_memory(self.__pid, INIT_NUMBER_OF_BOMBS_ADDRESS, new_number_of_bombs, 1)
        write_process_memory(self.__pid, NUMBER_OF_SAFE_PLACES_ADDRESS, self.get_board_size()[0]*self.get_board_size()[1] - new_number_of_bombs, 2)

    def count_backward(self, start):
        cur_time = start
        self.change_timer(cur_time)
        t = threading.Thread(target=self.ignore_click)
        t.start()
        self.stop_timer()
        while cur_time > 0:
            self.change_timer(cur_time - 1)
            self.redraw_window()
            cur_time -= 1
            time.sleep(1)
        t.join()

    def ignore_click(self):
        while self.get_timer() > 0:
            write_process_memory(self.__pid, DISABLE_CLICK_FLAG_ADDRESS, 1, 1)
        write_process_memory(self.__pid, DISABLE_CLICK_FLAG_ADDRESS, 0, 1)

    def set_best_times(self, difficulty, name, score):
        write_process_memory(self.__pid, BEST_TIMES_ADDRESS[MODE_TO_NUMBER[difficulty]], score, 2)
        for index in range(MAX_NAME_LENGTH):
            try:
                write_process_memory(self.__pid, BEST_TIME_NAMES_ADDRESS[MODE_TO_NUMBER[difficulty]] + 2 * index, ord(name[index]), 1)
            except IndexError:
                write_process_memory(self.__pid, BEST_TIME_NAMES_ADDRESS[MODE_TO_NUMBER[difficulty]] + 2 * index, 0, 1)

    def is_in_middle_of_game(self):
        status = read_process_memory(self.__pid, RUNNING_FLAG, 1)
        if status == 1:
            status_game_by_memory = True
        else:
            status_game_by_memory = False
        for row in self.get_board():
            for square in row:
                if square not in START_GAME_SQUARES:
                    return False
        return status_game_by_memory

    def set_in_middle_of_game(self, in_middle_of_game: bool):
        if in_middle_of_game:
            flag = 0x01
        else:
            flag = 0x10
        write_process_memory(self.__pid, RUNNING_FLAG, flag, 1)

    def restart_game(self, board, number_of_bombs):
        self.set_number_of_bombs(number_of_bombs)
        self.set_board(board)
        self.change_timer(0)
        self.start_timer()
        self.redraw_window()

    def redraw_window(self):
        hwnd = self.get_window_handle()
        user32 = ctypes.WinDLL("user32.dll")
        user32.ShowWindow(hwnd, SW_HIDE)
        user32.ShowWindow(hwnd, SW_SHOW)

    def get_window_handle(self):
        """The challenge: to find the windows belonging to the process you've just kicked off.
The idea is that if, for example, you run a notepad session, you then want to read the text entered into it,
 or close it down if it's been open too long, or whatever.
  The problem is that Windows doesn't provide a straightforward mapping from process id to window.
The situation is complicated because some process may not have a window, or may have several.
 The approach below uses the venerable technique of iterating over all top-level windows and finding the ones belonging to a process id.
  It only considers windows which are visible and enabled (which is generally what you want)
   and returns a list of the ones associated with your pid.
The test code runs up a notepad session using subprocess and passes its pid along after a couple of seconds,
 since experience showed that firing off the search too soon wouldn't find the window.
  Obviously, your own code could do whatever you wanted with the window."""
        def callback(hwnd, hwnds):
            if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
                _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
                if found_pid == self.__pid:
                    hwnds.append(hwnd)
            return True
        hwnds = []
        win32gui.EnumWindows(callback, hwnds)
        return hwnds[0]

    def get_clicked_squares(self):
        number_of_clicks = 0
        board = self.get_board()
        clicked_board = [[]]
        for row in range(len(board)):
            for column in range(len(board[0])):
                if board[row][column] in RIGHT_CLICKS_SQUARES:
                    number_of_clicks += 1
                    clicked_board[row].append(CLICKED)
                else:
                    clicked_board[row].append(NOT_CLICKED)
            clicked_board.append([])
        clicked_board.pop()
        return clicked_board, number_of_clicks


    def __repr__(self):
        return f"Pid: {self.__pid}           Mode: {NUMBER_TO_MODE[str(self.get_mode())]}           Size: {self.get_board_size()[0]} on {self.get_board_size()[1]}           Number Of Bombs: {self.get_number_of_bombs()}"
