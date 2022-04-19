
from utils.program import Program


def main():
    program = Program()
    try:
        program.run()
    except Exception as e:
        program.exit()


if __name__ == '__main__':
    main()
