from constants import MAX_PERCENTAGE, RIGHT_CLICKS_SQUARES, MAX_TIME, POINTS_PER_REVEALED_SQUARE, PROPORTION, \
    PROPORTION_BETWEEN_LOSE_AND_WIN


def calculate_rank(xp):
    return int((xp / 100)**0.5)


def calculate_game_point_win(revealed_squares_board, time):
    revealed_squares = 0
    for row in range(len(revealed_squares_board)):
        for column in range(len(revealed_squares_board[0])):
            if revealed_squares_board[row][column] == 1:
                revealed_squares += 1
    return int((POINTS_PER_REVEALED_SQUARE * revealed_squares + (MAX_TIME - time))//PROPORTION)


def calculate_game_point_lose(revealed_squares_board, time):
    revealed_squares = 0
    for row in range(len(revealed_squares_board)):
        for column in range(len(revealed_squares_board[0])):
            if revealed_squares_board[row][column] == 1:
                revealed_squares += 1
    return int(((-(((len(revealed_squares_board[0]) * len(revealed_squares_board))-POINTS_PER_REVEALED_SQUARE)
             * revealed_squares + (MAX_TIME - time)))//PROPORTION)//PROPORTION_BETWEEN_LOSE_AND_WIN)


def calculate_max_bombs(width, height):
    return (width * height) - (width + height) + 1


def calculate_number_of_bombs(board):
    number_of_bombs = 0
    for row in board:
        for square in row:
            if square == "HIDDEN_BOMB":
                number_of_bombs += 1
    return number_of_bombs


def calculate_bombs_percentage(bombs_counter, width, height):
    return int(MAX_PERCENTAGE - (bombs_counter / calculate_max_bombs(width, height) * MAX_PERCENTAGE))


def calculate_number_of_safe_squares(board):
    return len(board)*len(board[0]) - calculate_number_of_bombs(board)


