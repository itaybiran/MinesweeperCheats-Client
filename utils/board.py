from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QPushButton
from PIL import Image

from utils.winmine_exe import WinmineExe

SQUARE_SIZE = 40
SYMBOL_TO_IMG_PATH = {
    "EMPTY_SQUARE": "./img/empty.png",
    "ONE": "./img/one.png",
    "TWO": "./img/two.png",
    "THREE": "./img/three.png",
    "FOUR": "./img/four.png",
    "FIVE": "./img/five.png",
    "SIX": "./img/six.png",
    "SEVEN": "./img/seven.png",
    "EIGHT": "./img/eight.png",
    "BOMB": "./img/bomb.png",
    "BOMB_YOU_TOUCHED": "./img/bomb.png",
    "BOMB_WITH_X": "./img/bomb.png",
    "HIDDEN_BOMB": "./img/button.png",
    "SAFE_PLACE": "./img/button.png",
    "RIGHT_FLAG": "./img/flag.png",
    "WRONG_FLAG": "./img/flag.png",
    "QUESTION_MARK": "./img/question_mark"
}

NUMBER_TO_ICON = {
    "0": "./img/empty.png",
    "1": "./img/one.png",
    "2": "./img/two.png",
    "3": "./img/three.png",
    "4": "./img/four.png",
    "5": "./img/five.png",
    "6": "./img/six.png",
    "7": "./img/seven.png",
    "8": "./img/eight.png",
    "bomb": "./img/bomb.png",
    "button": "./img/button.png"
}


def add_button(parent, type, x, y):
    button = QPushButton("", parent)
    button.setVisible(True)
    button.move(x, y)
    button.setFixedHeight(24)
    button.setFixedWidth(24)
    button.setIcon(QIcon(NUMBER_TO_ICON[str(type)]))
    button.setStyleSheet(
        "background-color:transparent;"
    )
    return button


def calculate_board(board: list):
    revealed_board = init_board(board)
    for row in range(len(board)):
        for column in range(len(board[row])):
            if board[row][column] == 'HIDDEN_BOMB' or board[row][column] == "RIGHT_FLAG":
                revealed_board[row][column] = "bomb"
                inc_around_bomb(revealed_board, row, column)
    return revealed_board


def inc_around_bomb(revealed_board, row, column):
    for i in range(row - 1, row + 2):
        for j in range(column - 1, column + 2):
            try:
                if revealed_board[i][j] != "bomb" and j >= 0 and i >= 0:
                    revealed_board[i][j] += 1
            except IndexError:
                pass


def init_board(board: list):
    revealed_board = [[]]
    for row in range(len(board)):
        for column in range(len(board[row])):
            revealed_board[row].append(0)
        revealed_board.append([])
    revealed_board.pop()
    return revealed_board


def init_board_img(width, height):
    board_img = Image.new('RGB', (width, height), (250, 250, 250))
    return board_img


def add_square(board_img, square_img_path, x, y):
    img = Image.open(square_img_path)
    board_img.paste(img, (x, y))


def create_board(matrix_board, path_to_save=""):
    board_img = init_board_img(SQUARE_SIZE * len(matrix_board[0]), SQUARE_SIZE * len(matrix_board))
    for row in range(len(matrix_board)):
        for column in range(len(matrix_board[row])):
            add_square(board_img, SYMBOL_TO_IMG_PATH[str(matrix_board[row][column])], column * SQUARE_SIZE,
                       row * SQUARE_SIZE)
    if path_to_save != "":
        board_img.save(path_to_save, "PNG")
    return board_img

