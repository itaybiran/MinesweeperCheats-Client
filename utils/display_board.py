from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QPushButton

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
