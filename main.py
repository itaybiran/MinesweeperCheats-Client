
from utils.program import Program


def main():
    try:
        program = Program()
        program.run()
    except Exception as e:
        print(e)
        program.exit()


if __name__ == '__main__':
    main()
