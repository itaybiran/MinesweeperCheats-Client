
from winreg import REG_DWORD, REG_SZ

# windows
WIDTH = 700
HEIGHT = 400
PID_INDEX = 9
DEFAULT_PID = 0
WINMINE_INDEX = 5
IMG_INDEX = 3
SQUARE_SIZE = 16

MAX_PERCENTAGE = 100

REVEAL_BOARD_STARTING_X_POSITION = 10
REVEAL_BOARD_STARTING_Y_POSITION = 10

CHANGE_BOARD_FIX_ALIGNMENT = 4
CHANGE_BOARD_UPPER_AREA_HEIGHT = 50
CHANGE_BOARD_LOWER_AREA_HEIGHT = 80
CHANGE_BOARD_MIN_WIDTH = 300
CHANGE_BOARD_DISTANCE_BETWEEN_BOARD_AND_UPPER_AREA = 10
CHANGE_BOARD_DISTANCE_BETWEEN_BOARD_AND_LOWER_AREA = 20
CHANGE_BOARD_DISTANCE_BETWEEN_BOARD_AND_WINDOW = 30

# winmine consts
MAX_TIME = 999
MIN_TIME = 0
INITIALIZE_TIME = 0
MAX_HEIGHT = 30
MAX_WIDTH = 24
MIN_NUM_OF_BOMBS = 10
MAX_NAME_LENGTH = 32
BAR_PIXELS_HEIGHT = 67
BAR_PIXELS_WIDTH = 24
WINMINE_REGISTRY_PATH = r"Software\Microsoft\winmine"
BYTES_TO_READ = {1: 'B', 2: 'H', 4: 'I', 6: 'L', 8: 'Q'}
DISABLE_CLICK_FLAG_ADDRESS = 0x01005148
MODE_ADDRESS = 0x010056A0
NUMBER_OF_SAFE_PLACES_ADDRESS = 0x010057A0
NUMBER_OF_BOMBS_ADDRESS = 0x01005194
INIT_NUMBER_OF_BOMBS_ADDRESS = 0x01005330
BOARD_HEIGHT_ADDRESS = 0x010056A8
BOARD_WIDTH_ADDRESS = 0x010056AC
SECONDS_COUNTER = 0x0100579c
TIMER_FLAG = 0x01005164
RUNNING_FLAG = 0x01005000
# FLAGS_USED_COUNTER = 0x01005338
BOARD_WIDTH_MENU_ADDRESS = 0x01005334
BOARD_HEIGHT_MENU_ADDRESS = 0x01005338
PIXELS_TO_DRAW_HEIGHT_ADDRESS = 0x01005B20
PIXELS_TO_DRAW_WIDTH_ADDRESS = 0x01005B2C
WINDOW_HANDLE_ADDRESS = 0x01005B24
FLAGS_LEFT_COUNTER = 0x01005194
BOARD_TOP_LEFT_CORNER = 0x01005361
BOARD_BOUNDARY_TOP_LEFT_CORNER_ADDRESS = 0x01005340
LAST_MEMORY_REPRESENTING_BOARD = 0x0100569F

VALUE_TO_SYMBOL = {0x8E: "RIGHT_FLAG",
                   0x0E: "WRONG_FLAG",
                   0x8D: "QUESTION_MARK",
                   0x0D: "QUESTION_MARK",
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
                   0x10: "BOUNDARY",
                   0x80: "EMPTY_SQUARE",
                   0x00: "EMPTY_SQUARE"
                   }

START_GAME_SQUARES = ["HIDDEN_BOMB", "SAFE_PLACE", "QUESTION_MARK", "WRONG_FLAG", "RIGHT_FLAG"]

UNUSED_AREA = 0x0F
BOUNDARY = 0x10
TWO_LINES = 0x20
CONVERT_TYPE = {"<class 'int'>": REG_DWORD,
                "<class 'str'>": REG_SZ}

BEST_TIME_EASY_ADDRESS = 0x010056CC
BEST_TIME_INTIMIDATE_ADDRESS = 0x010056D0
BEST_TIME_EXPERT_ADDRESS = 0x010056D4

BEST_TIME_NAME_EASY_ADDRESS = 0x010056D8
BEST_TIME_NAME_INTIMIDATE_ADDRESS = 0x01005718
BEST_TIME_NAME_EXPERT_ADDRESS = 0x01005758

EASY_MODE = 0
INTIMIDATE_MODE = 1
EXPERT_MODE = 2
CUSTOM_MODE = 3

MODE_TO_NUMBER = {"Easy": EASY_MODE,
                  "Intermediate": INTIMIDATE_MODE,
                  "Expert": EXPERT_MODE,
                  "Custom": CUSTOM_MODE}

NUMBER_TO_MODE = {"0": "easy",
                  "1": "intimidate",
                  "2": "expert",
                  "3": "custom"}

BEST_TIMES_ADDRESS = {EASY_MODE: BEST_TIME_EASY_ADDRESS,
                      INTIMIDATE_MODE: BEST_TIME_INTIMIDATE_ADDRESS,
                      EXPERT_MODE: BEST_TIME_EXPERT_ADDRESS}
BEST_TIME_NAMES_ADDRESS = {EASY_MODE: BEST_TIME_NAME_EASY_ADDRESS,
                           INTIMIDATE_MODE: BEST_TIME_NAME_INTIMIDATE_ADDRESS,
                           EXPERT_MODE: BEST_TIME_NAME_EXPERT_ADDRESS}

# board
SQUARE_SIZE_TOOLTIP = 40
SQUARE_BUTTON_SIZE = 24
SYMBOL_TO_IMG_PATH = {
    "EMPTY_SQUARE": "./img/board-icons/empty.png",
    "ONE": "./img/board-icons/one.png",
    "TWO": "./img/board-icons/two.png",
    "THREE": "./img/board-icons/three.png",
    "FOUR": "./img/board-icons/four.png",
    "FIVE": "./img/board-icons/five.png",
    "SIX": "./img/board-icons/six.png",
    "SEVEN": "./img/board-icons/seven.png",
    "EIGHT": "./img/board-icons/eight.png",
    "BOMB": "./img/board-icons/bomb.png",
    "BOMB_YOU_TOUCHED": "./img/board-icons/bomb.png",
    "BOMB_WITH_X": "./img/board-icons/bomb.png",
    "HIDDEN_BOMB": "./img/board-icons/button.png",
    "SAFE_PLACE": "./img/board-icons/button.png",
    "RIGHT_FLAG": "./img/board-icons/flag.png",
    "WRONG_FLAG": "./img/board-icons/flag.png",
    "QUESTION_MARK": "./img/board-icons/question_mark.png"
}
NUMBER_TO_ICON = {
    "0": "./img/board-icons/empty.png",
    "1": "./img/board-icons/one.png",
    "2": "./img/board-icons/two.png",
    "3": "./img/board-icons/three.png",
    "4": "./img/board-icons/four.png",
    "5": "./img/board-icons/five.png",
    "6": "./img/board-icons/six.png",
    "7": "./img/board-icons/seven.png",
    "8": "./img/board-icons/eight.png",
    "bomb": "./img/board-icons/bomb.png",
    "button": "./img/board-icons/button.png"
}

# process manager

PIDS_FILE_PATH = "pids.txt"
WRITE_AND_READ_PERMISSION = "r+"
PID = 0
STATUS = 1
AVAILABLE = "0"
NOT_AVAILABLE = "1"

# Networking
SERVER_URL = "http://127.0.0.1:8000"
STATUS_CODE_OK = 200
STATUS_CODE_BAD_REQUEST = 401
