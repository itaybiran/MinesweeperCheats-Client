
from PyQt5.QtGui import QIcon
from PIL import Image
from constants import NUMBER_TO_ICON, SQUARE_SIZE_TOOLTIP, SYMBOL_TO_IMG_PATH, SQUARE_BUTTON_SIZE

from utils.button import CustomButton


def add_button(parent, type_of_square, x, y):
    button: CustomButton = CustomButton("", parent)
    button.setVisible(True)
    button.move(x, y)
    button.setFixedHeight(SQUARE_BUTTON_SIZE)
    button.setFixedWidth(SQUARE_BUTTON_SIZE)
    button.setIcon(QIcon(NUMBER_TO_ICON[str(type_of_square)]))
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


def create_board(matrix_board=[[]], path_to_save=""):
    try:
        board_img = init_board_img(SQUARE_SIZE_TOOLTIP * len(matrix_board[0]), SQUARE_SIZE_TOOLTIP * len(matrix_board))
        for row in range(len(matrix_board)):
            for column in range(len(matrix_board[row])):
                add_square(board_img, SYMBOL_TO_IMG_PATH[str(matrix_board[row][column])], column * SQUARE_SIZE_TOOLTIP,
                           row * SQUARE_SIZE_TOOLTIP)
        if path_to_save != "":
            board_img.save(path_to_save, "PNG")
        return board_img
    except:
        pass


def create_clicked_board(matrix_clicked_board=[[]], path_to_save=""):
    try:
        board_img = init_board_img(SQUARE_SIZE_TOOLTIP * len(matrix_clicked_board[0]), SQUARE_SIZE_TOOLTIP * len(matrix_clicked_board))
        for row in range(len(matrix_clicked_board)):
            for column in range(len(matrix_clicked_board[row])):
                if str(matrix_clicked_board[row][column]) == "1":
                    add_square(board_img, "./img/board-icons/clicked.png", column * SQUARE_SIZE_TOOLTIP, row * SQUARE_SIZE_TOOLTIP)
                else:
                    add_square(board_img, "./img/board-icons/button.png", column * SQUARE_SIZE_TOOLTIP, row * SQUARE_SIZE_TOOLTIP)
        if path_to_save != "":
            board_img.save(path_to_save, "PNG")
        return board_img
    except:
        pass
