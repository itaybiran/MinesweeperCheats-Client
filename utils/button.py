from PyQt5.QtWidgets import QPushButton


class CustomButton(QPushButton):
    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.__status = False

    def get_status(self):
        return self.__status

    def change_status(self):
        self.__status = not self.__status
