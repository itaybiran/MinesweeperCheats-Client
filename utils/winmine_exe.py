
import threading
import time
from winreg import *
from constants import *
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

    def get_timer(self):
        return read_process_memory(self.__pid, SECONDS_COUNTER, 1)

    def stop_timer(self):
        write_process_memory(self.__pid, TIMER_FLAG, 0, 1)

    def start_timer(self):
        write_process_memory(self.__pid, TIMER_FLAG, 1, 1)

    def get_board(self):
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
        write_process_memory(self.__pid, 0x010056A4, new_number_of_bombs, 1)
        write_process_memory(self.__pid, NUMBER_OF_BOMBS_ADDRESS, new_number_of_bombs, 1)
        write_process_memory(self.__pid, INIT_NUMBER_OF_BOMBS_ADDRESS, new_number_of_bombs, 1)

    def count_backward(self, start):
        cur_time = start
        self.change_timer(self.__pid, cur_time)
        t = threading.Thread(target=self.ignore_click, args=[self.__pid])
        t.start()
        while cur_time > 0:
            self.stop_timer(self.__pid)
            self.change_timer(self.__pid, cur_time - 1)
            self.start_timer(self.__pid)
            cur_time -= 1
            time.sleep(1)
        t.join()

    def ignore_click(self):
        while self.get_timer(self.__pid) > 0:
            write_process_memory(self.__pid, DISABLE_CLICK_FLAG_ADDRESS, 1, 1)
        write_process_memory(self.__pid, DISABLE_CLICK_FLAG_ADDRESS, 0, 1)

    def set_best_times(self, difficulty, name, score):
        a = 0x010056D9
        write_process_memory(self.__pid, BEST_TIMES_ADDRESS[MODE_TO_NUMBER[difficulty]], score, 2)
        for index in range(MAX_NAME_LENGTH):
            try:
                write_process_memory(self.__pid,a + 2 * index, 0, 1)
                write_process_memory(self.__pid, BEST_TIME_NAMES_ADDRESS[MODE_TO_NUMBER[difficulty]] + 2 * index, ord(name[index]), 1)
            except IndexError:
                write_process_memory(self.__pid, BEST_TIME_NAMES_ADDRESS[MODE_TO_NUMBER[difficulty]] + 2 * index, 0, 1)

    def __repr__(self):
        return f"Pid: {self.__pid}           Mode: {NUMBER_TO_MODE[str(self.get_mode())]}           Size: {self.get_board_size()[0]} on {self.get_board_size()[1]}           Number Of Bombs: {self.get_number_of_bombs()}"