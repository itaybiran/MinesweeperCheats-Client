
def calculate_rank(xp):
    return int((xp / 100) ** 0.5)


def calculate_max_bombs(width, height):
    return (width * height) - (width + height) + 1


def calculate_number_of_bombs(board):
    number_of_bombs = 0
    for row in board:
        for square in row:
            if square == "HIDDEN_BOMB":
                number_of_bombs += 1
    return number_of_bombs
