
def calculate_rank(xp):
    return int((xp / 100) ** 0.5)


def calculate_max_bombs(width, height):
    return (width * height) - (width + height) + 1
