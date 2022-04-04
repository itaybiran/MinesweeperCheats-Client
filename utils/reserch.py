import codecs
import os
import ctypes
import struct
import threading
import time
from msilib.schema import Registry
from winreg import *

import timer

ConnectRegistry(None, HKEY_LOCAL_MACHINE)

from win32con import PROCESS_VM_READ, PROCESS_ALL_ACCESS, SW_SHOW

MAX_HEIGHT = 30
MAX_WIDTH = 24
MAX_NAME_LENGTH = 32
WINMINE_REGISTRY_PATH = r"Software\Microsoft\winmine"
BYTES_TO_READ = {1: 'B', 2: 'H', 4: 'I', 6: 'L', 8: 'Q'}
kernel32 = ctypes.WinDLL("kernel32.dll")
user32 = ctypes.WinDLL("user32.dll")
DISABLE_CLICK_FLAG_ADDRESS = 0x01005148
MODE_ADDRESS = 0x010056A0
NUMBER_OF_BOMBS_ADDRESS = 0x01005194
INIT_NUMBER_OF_BOMBS_ADDRESS = 0x01005330
BOARD_HEIGHT_ADDRESS = 0x010056A8
BOARD_WIDTH_ADDRESS = 0x010056AC
SECONDS_COUNTER = 0x0100579c
TIMER_FLAG = 0x01005164
# FLAGS_USED_COUNTER = 0x01005338
BOARD_WIDTH_MENU_ADDRESS = 0x01005334
BOARD_HEIGHT_MENU_ADDRESS = 0x01005338
FLAGS_LEFT_COUNTER = 0x01005194
BOARD_TOP_LEFT_CORNER = 0x01005361
BOARD_BOUNDARY_TOP_LEFT_CORNER_ADDRESS = 0x01005340
LAST_MEMORY_REPRESENTING_BOARD = 0x0100569F

VALUE_TO_SYMBOL = {0x8E: "RIGHT_FLAG",
                   0x0E: "WRONG_FLAG",
                   0x8D: "QUESTION_MARK",
                   0x8F: "HIDDEN_BOMB",
                   0xCC: "BOMB_YOU_TOUCHED",
                   0x0B: "BOMB_WITH_X",
                   0x8A: "BOMB",
                   0x0F: "SAFE_PLACE",
                   0X40: "EMPTY_SQUARE",
                   0x41: "ONE",
                   0x42: "TWO",
                   0x43: "THREE",
                   0x44: "FOUR",
                   0x45: "FIVE",
                   0x46: "SIX",
                   0x47: "SEVEN",
                   0x48: "EIGHT",
                   0x10: "BOUNDARY"
                   }

UNUSED_AREA = 0x0F
BOUNDARY = 0x10
TWO_LINES = 0x20
CONVERT_TYPE = {"<class 'int'>": REG_DWORD,
                "<class 'str'>": REG_SZ}

BEST_TIME_EASY_ADDRESS = 0x010056CD
BEST_TIME_INTIMIDATE_ADDRESS = 0x010056D0
BEST_TIME_EXPERT_ADDRESS = 0x010056D4

BEST_TIME_NAME_EASY_ADDRESS = 0x010056D9
BEST_TIME_NAME_INTIMIDATE_ADDRESS = 0x01005718
BEST_TIME_NAME_EXPERT_ADDRESS = 0x01005758

EASY_MODE = 0
INTIMIDATE_MODE = 1
EXPERT_MODE = 2
BEST_TIMES_ADDRESS = {EASY_MODE: BEST_TIME_EASY_ADDRESS,
                      INTIMIDATE_MODE: BEST_TIME_INTIMIDATE_ADDRESS,
                      EXPERT_MODE: BEST_TIME_EXPERT_ADDRESS}
BEST_TIME_NAMES_ADDRESS = {EASY_MODE: BEST_TIME_NAME_EASY_ADDRESS,
                           INTIMIDATE_MODE: BEST_TIME_NAME_INTIMIDATE_ADDRESS,
                           EXPERT_MODE: BEST_TIME_NAME_EXPERT_ADDRESS}


def get_process_pid(process_name):
    """A function that returns True and the pid of a process if it is currently running,
     or False and -1 if it is not."""
    command = "tasklist | findstr " + process_name
    try:
        process_description_line = os.popen(command).read()
        pid = int(process_description_line.split()[1])
        return True, pid
    except IndexError as e:
        return False, -1


def write_process_memory(pid, memory_address, data, bytes_to_write):
    """A function that gets a pid of a process, a memory address, data and a number of bytes,
     and writes the data to the specified address."""
    data_in_bytes = data.to_bytes(bytes_to_write, byteorder="little")
    handle = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
    buffer = ctypes.create_string_buffer(data_in_bytes)
    value = kernel32.WriteProcessMemory(handle, memory_address, buffer, bytes_to_write, None)
    kernel32.CloseHandle(handle)


def read_process_memory(pid, memory_address, number_of_bytes_to_read):
    """A function that gets a pid of a process, a memory address and a number of bytes,
     and returns the value of the specified bytes."""
    handle = kernel32.OpenProcess(PROCESS_VM_READ, False, pid)
    buffer = (ctypes.c_byte * number_of_bytes_to_read)()
    bytes_read = ctypes.c_ulonglong()
    value = kernel32.ReadProcessMemory(handle, memory_address, buffer, number_of_bytes_to_read,
                                       ctypes.byref(bytes_read))
    kernel32.CloseHandle(handle)
    return struct.unpack(BYTES_TO_READ[number_of_bytes_to_read], buffer)[0]


class WinmineExe(object):
    def __init__(self, pid):
        self.pid = pid

    def change_timer(self, new_time):
        write_process_memory(self.pid, SECONDS_COUNTER, new_time, 2)

    def get_timer(self):
        return read_process_memory(self.pid, SECONDS_COUNTER, 1)

    def stop_timer(self):
        write_process_memory(self.pid, TIMER_FLAG, 0, 1)

    def start_timer(self):
        write_process_memory(self.pid, TIMER_FLAG, 1, 1)

    """    def set_board_easy(self, board):
            A function that gets a board and sets the game to this board.
            for row_index, row in enumerate(board):
                for column_index, square in enumerate(row):
                    memory_address = BOARD_TOP_LEFT_CORNER + column_index + row_index * 0x20
                    write_process_memory(pid, memory_address,
                                         list(VALUE_TO_SYMBOL.keys())[list(VALUE_TO_SYMBOL.values()).index(square)], 1)
    """

    def get_board(self):
        """A function that returns a matrix represents the board."""
        board = [[]]
        row, column = 0, 0
        height, width = self.get_board_size()
        for row in range(height):
            for column in range(width):
                memory_address = BOARD_TOP_LEFT_CORNER + column + (row * TWO_LINES)
                current_block = read_process_memory(self.pid, memory_address, 1)
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
            write_process_memory(self.pid, memory_address, UNUSED_AREA, 1)
        # Sets the top boundary
        for memory_address in range(BOARD_BOUNDARY_TOP_LEFT_CORNER_ADDRESS,
                                    BOARD_BOUNDARY_TOP_LEFT_CORNER_ADDRESS + width + 2):
            write_process_memory(self.pid, memory_address, BOUNDARY, 1)
        # Sets the bottom boundary
        for memory_address in range(BOARD_BOUNDARY_TOP_LEFT_CORNER_ADDRESS + (height + 1) * TWO_LINES,
                                    BOARD_BOUNDARY_TOP_LEFT_CORNER_ADDRESS + (height + 1) * TWO_LINES + width + 2):
            write_process_memory(self.pid, memory_address, BOUNDARY, 1)
        # Sets the body of the board
        for row in range(height):
            memory_address = BOARD_TOP_LEFT_CORNER + row * TWO_LINES - 1
            write_process_memory(self.pid, memory_address, BOUNDARY, 1)
            for column in range(width):
                memory_address = BOARD_TOP_LEFT_CORNER + column + row * TWO_LINES
                write_process_memory(self.pid, memory_address,
                                     list(VALUE_TO_SYMBOL.keys())[
                                         list(VALUE_TO_SYMBOL.values()).index(board[row][column])],
                                     1)
            memory_address = BOARD_TOP_LEFT_CORNER + width + row * TWO_LINES
            write_process_memory(self.pid, memory_address, BOUNDARY, 1)

    def get_board_size(self):
        height = read_process_memory(self.pid, BOARD_HEIGHT_ADDRESS, 1)
        width = read_process_memory(self.pid, BOARD_WIDTH_ADDRESS, 1)
        return height, width

    def set_board_size(self, height, width):
        write_process_memory(self.pid, BOARD_WIDTH_MENU_ADDRESS, height, 1)
        write_process_memory(self.pid, BOARD_HEIGHT_MENU_ADDRESS, height, 1)
        write_process_memory(self.pid, BOARD_HEIGHT_ADDRESS, height, 1)
        write_process_memory(self.pid, BOARD_WIDTH_ADDRESS, width, 1)

    def write_to_winmine_registry(self, key, new_value):
        key_handle = OpenKey(HKEY_CURRENT_USER, WINMINE_REGISTRY_PATH, 0, KEY_ALL_ACCESS)
        SetValueEx(key_handle, key, 0, CONVERT_TYPE[str(type(new_value))], new_value)

    def change_best_time(self, difficulty, player_name, new_time):
        self.write_to_winmine_registry("Time" + str(difficulty), new_time)
        self.write_to_winmine_registry("Name" + str(difficulty), player_name[0: MAX_NAME_LENGTH])

    def get_mode(self):
        return read_process_memory(self.pid, MODE_ADDRESS, 1)

    def set_mode(self, mode):
        write_process_memory(self.pid, MODE_ADDRESS, mode, 1)

    def get_number_of_bombs(self):
        return read_process_memory(self.pid, NUMBER_OF_BOMBS_ADDRESS, 1)

    def set_number_of_bombs(self, new_number_of_bombs):
        write_process_memory(self.pid, 0x010056A4, new_number_of_bombs, 1)
        write_process_memory(self.pid, NUMBER_OF_BOMBS_ADDRESS, new_number_of_bombs, 1)
        write_process_memory(self.pid, INIT_NUMBER_OF_BOMBS_ADDRESS, new_number_of_bombs, 1)

    def count_backward(self, start):
        cur_time = start
        self.change_timer(self.pid, cur_time)
        t = threading.Thread(target=self.ignore_click, args=[self.pid])
        t.start()
        while cur_time > 0:
            self.stop_timer(self.pid)
            self.change_timer(self.pid, cur_time - 1)
            self.start_timer(self.pid)
            cur_time -= 1
            time.sleep(1)
        t.join()

    def ignore_click(self):
        while self.get_timer(self.pid) > 0:
            write_process_memory(self.pid, DISABLE_CLICK_FLAG_ADDRESS, 1, 1)
        write_process_memory(self.pid, DISABLE_CLICK_FLAG_ADDRESS, 0, 1)

    def set_best_times(self, difficulty, name, score):
        write_process_memory(self.pid, BEST_TIMES_ADDRESS[difficulty], score, 2)
        for index in range(MAX_NAME_LENGTH):
            try:
                write_process_memory(self.pid, BEST_TIME_NAMES_ADDRESS[difficulty] + 2 * index, ord(name[index]), 1)
            except:
                write_process_memory(self.pid, BEST_TIME_NAMES_ADDRESS[difficulty] + 2 * index, 0, 1)


"""
    def redraw_game():
        #get handle somehow
        window_handle = 
        user32.ShowWindow(,SW_SHOWMINIMIZED)
        user32.ShowWindow(,SW_SHOW)
"""


def main():
    pid = get_process_pid("Winmine__XP.exe")[1]
    board = [
        ['SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE',
         'SAFE_PLACE'],
        ['HIDDEN_BOMB', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE',
         'SAFE_PLACE', 'SAFE_PLACE'],
        ['SAFE_PLACE', 'HIDDEN_BOMB', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE',
         'SAFE_PLACE', 'SAFE_PLACE'],
        ['HIDDEN_BOMB', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE',
         'SAFE_PLACE', 'SAFE_PLACE'],
        ['SAFE_PLACE', 'HIDDEN_BOMB', 'HIDDEN_BOMB', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE',
         'SAFE_PLACE', 'SAFE_PLACE'],
        ['SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE',
         'SAFE_PLACE'],
        ['SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE',
         'SAFE_PLACE'],
        ['HIDDEN_BOMB', 'HIDDEN_BOMB', 'SAFE_PLACE', 'SAFE_PLACE', 'HIDDEN_BOMB', 'SAFE_PLACE', 'SAFE_PLACE',
         'SAFE_PLACE', 'SAFE_PLACE'],
        ['SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'HIDDEN_BOMB', 'HIDDEN_BOMB',
         'SAFE_PLACE', 'SAFE_PLACE']]
    board_expert = [['HIDDEN_BOMB', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'HIDDEN_BOMB', 'SAFE_PLACE',
                     'HIDDEN_BOMB', 'HIDDEN_BOMB', 'HIDDEN_BOMB', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE',
                     'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'HIDDEN_BOMB',
                     'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE',
                     'SAFE_PLACE', 'HIDDEN_BOMB', 'HIDDEN_BOMB'],
                    ['SAFE_PLACE', 'SAFE_PLACE', 'HIDDEN_BOMB', 'SAFE_PLACE', 'HIDDEN_BOMB', 'SAFE_PLACE', 'SAFE_PLACE',
                     'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'HIDDEN_BOMB', 'SAFE_PLACE', 'HIDDEN_BOMB', 'SAFE_PLACE',
                     'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE',
                     'SAFE_PLACE', 'SAFE_PLACE', 'HIDDEN_BOMB', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'HIDDEN_BOMB',
                     'HIDDEN_BOMB', 'SAFE_PLACE'],
                    ['SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE',
                     'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'HIDDEN_BOMB', 'SAFE_PLACE', 'SAFE_PLACE',
                     'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'HIDDEN_BOMB', 'HIDDEN_BOMB',
                     'HIDDEN_BOMB', 'SAFE_PLACE', 'HIDDEN_BOMB', 'SAFE_PLACE', 'SAFE_PLACE', 'HIDDEN_BOMB',
                     'HIDDEN_BOMB', 'SAFE_PLACE', 'SAFE_PLACE'],
                    ['HIDDEN_BOMB', 'HIDDEN_BOMB', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE',
                     'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE',
                     'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE',
                     'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'HIDDEN_BOMB',
                     'SAFE_PLACE', 'SAFE_PLACE'],
                    ['HIDDEN_BOMB', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'HIDDEN_BOMB', 'SAFE_PLACE',
                     'SAFE_PLACE', 'SAFE_PLACE', 'HIDDEN_BOMB', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE',
                     'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'HIDDEN_BOMB', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE',
                     'SAFE_PLACE', 'SAFE_PLACE', 'HIDDEN_BOMB', 'HIDDEN_BOMB', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE',
                     'SAFE_PLACE', 'HIDDEN_BOMB'],
                    ['SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE',
                     'SAFE_PLACE', 'HIDDEN_BOMB', 'SAFE_PLACE', 'HIDDEN_BOMB', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE',
                     'SAFE_PLACE', 'HIDDEN_BOMB', 'SAFE_PLACE', 'SAFE_PLACE', 'HIDDEN_BOMB', 'SAFE_PLACE', 'SAFE_PLACE',
                     'HIDDEN_BOMB', 'SAFE_PLACE', 'HIDDEN_BOMB', 'HIDDEN_BOMB', 'SAFE_PLACE', 'SAFE_PLACE',
                     'SAFE_PLACE', 'HIDDEN_BOMB', 'SAFE_PLACE'],
                    ['SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE',
                     'SAFE_PLACE', 'SAFE_PLACE', 'HIDDEN_BOMB', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE',
                     'SAFE_PLACE', 'HIDDEN_BOMB', 'SAFE_PLACE', 'HIDDEN_BOMB', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE',
                     'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE',
                     'SAFE_PLACE', 'SAFE_PLACE'],
                    ['HIDDEN_BOMB', 'HIDDEN_BOMB', 'HIDDEN_BOMB', 'SAFE_PLACE', 'SAFE_PLACE', 'HIDDEN_BOMB',
                     'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'HIDDEN_BOMB', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE',
                     'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'HIDDEN_BOMB', 'SAFE_PLACE',
                     'SAFE_PLACE', 'HIDDEN_BOMB', 'HIDDEN_BOMB', 'HIDDEN_BOMB', 'SAFE_PLACE', 'SAFE_PLACE',
                     'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE'],
                    ['HIDDEN_BOMB', 'SAFE_PLACE', 'HIDDEN_BOMB', 'HIDDEN_BOMB', 'SAFE_PLACE', 'SAFE_PLACE',
                     'HIDDEN_BOMB', 'HIDDEN_BOMB', 'SAFE_PLACE', 'HIDDEN_BOMB', 'SAFE_PLACE', 'HIDDEN_BOMB',
                     'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'HIDDEN_BOMB', 'SAFE_PLACE',
                     'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'HIDDEN_BOMB', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE',
                     'SAFE_PLACE', 'SAFE_PLACE', 'HIDDEN_BOMB', 'SAFE_PLACE'],
                    ['HIDDEN_BOMB', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'HIDDEN_BOMB', 'SAFE_PLACE',
                     'HIDDEN_BOMB', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'HIDDEN_BOMB',
                     'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'HIDDEN_BOMB', 'SAFE_PLACE', 'SAFE_PLACE',
                     'HIDDEN_BOMB', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE',
                     'SAFE_PLACE', 'SAFE_PLACE'],
                    ['SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE',
                     'HIDDEN_BOMB', 'HIDDEN_BOMB', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE',
                     'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'HIDDEN_BOMB', 'HIDDEN_BOMB',
                     'HIDDEN_BOMB', 'HIDDEN_BOMB', 'HIDDEN_BOMB', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE',
                     'SAFE_PLACE', 'SAFE_PLACE', 'HIDDEN_BOMB'],
                    ['SAFE_PLACE', 'SAFE_PLACE', 'HIDDEN_BOMB', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE',
                     'HIDDEN_BOMB', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE',
                     'SAFE_PLACE', 'SAFE_PLACE', 'HIDDEN_BOMB', 'SAFE_PLACE', 'SAFE_PLACE', 'HIDDEN_BOMB', 'SAFE_PLACE',
                     'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE',
                     'SAFE_PLACE', 'SAFE_PLACE'],
                    ['SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'HIDDEN_BOMB', 'SAFE_PLACE', 'SAFE_PLACE', 'HIDDEN_BOMB',
                     'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE',
                     'SAFE_PLACE', 'SAFE_PLACE', 'HIDDEN_BOMB', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE',
                     'SAFE_PLACE', 'SAFE_PLACE', 'HIDDEN_BOMB', 'SAFE_PLACE', 'SAFE_PLACE', 'HIDDEN_BOMB', 'SAFE_PLACE',
                     'SAFE_PLACE', 'SAFE_PLACE'],
                    ['SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'HIDDEN_BOMB', 'SAFE_PLACE',
                     'SAFE_PLACE', 'HIDDEN_BOMB', 'HIDDEN_BOMB', 'SAFE_PLACE', 'HIDDEN_BOMB', 'SAFE_PLACE',
                     'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE',
                     'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE',
                     'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE'],
                    ['SAFE_PLACE', 'HIDDEN_BOMB', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE',
                     'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'HIDDEN_BOMB',
                     'SAFE_PLACE', 'SAFE_PLACE', 'HIDDEN_BOMB', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE',
                     'SAFE_PLACE', 'SAFE_PLACE', 'HIDDEN_BOMB', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE',
                     'HIDDEN_BOMB', 'HIDDEN_BOMB'],
                    ['SAFE_PLACE', 'SAFE_PLACE', 'HIDDEN_BOMB', 'HIDDEN_BOMB', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE',
                     'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE',
                     'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'HIDDEN_BOMB', 'SAFE_PLACE',
                     'HIDDEN_BOMB', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE', 'SAFE_PLACE',
                     'SAFE_PLACE', 'SAFE_PLACE']]
    # board = get_board(pid)
    # set_board_size(pid, 16, 30)
    # set_mode(pid, 2)
    # set_board(pid, board_expert)
    # set_best_times(pid, 1, "row", 43534)
    # write_process_memory(pid, 0x01005b20, 0X143, 2)
    # write_process_memory(pid, 0x01005b2c, 0X1f8, 2)
    winmine = WinmineExe(pid)
    winmine.start_timer(pid)

    # write_process_memory(pid, 0x01005b88, 0X4d, 1)

    # print(get_board(pid))
    # for i in board:
    #    print(i)
    # set_number_of_bombs(pid, 44)
    # count_backward(pid, 10)
    # write_process_memory(pid, 0X01006920, 9, 10)
    # print(str(get_board_easy(pid)) + "\n" + str(get_board_size(pid)) + "\n" + str(get_mode(pid)) + "\n" + str(get_number_of_bombs(pid)) + "\n")
    # set_mode(pid, 3)
    # set_board_size(pid, 13,12)


if __name__ == '_main_':
    main()
