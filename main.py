import sys

from PyQt5.QtWidgets import QWidget, QApplication, QStackedWidget, QDialog
from PyQt5.uic import loadUi
from reserch import *

pid = get_process_pid("Winmine__XP.exe")[1]
MAX_TIME = 999
MIN_TIME = 0
INITIALIZE_TIME = 0


class CheatsWidget(QWidget):

    def __init__(self):
        super(CheatsWidget, self).__init__()
        loadUi("gui/cheats_widget.ui", self)
        self.ChangeTimeButton.clicked.connect(self.show_change_time_dialog)
        self.InitializeTimerButton.clicked.connect(self.initialize_timer_button)
        self.ActiveTimerButton.toggled.connect(self.active_timer_button)
        self.ActiveTimerButton.setChecked(True)

    def show_change_time_dialog(self):
        change_time_dialog = ChangeTimeDialog()
        change_time_dialog.exec()

    def initialize_timer_button(self):
        change_timer(pid, INITIALIZE_TIME)

    def active_timer_button(self):
        if self.ActiveTimerButton.isChecked():
            start_timer(pid)
        else:
            stop_timer(pid)


class ChangeTimeDialog(QDialog):
    def __init__(self):
        super(ChangeTimeDialog, self).__init__()
        loadUi("gui/change_time_dialog.ui", self)
        self.OkButton.clicked.connect(self.change_time)

    def change_time(self):
        new_time = self.ChangeTimeTextField.text()
        if new_time.isnumeric() and MIN_TIME <= int(new_time) <= MAX_TIME:
            change_timer(pid, int(new_time))
            self.close()
        else:
            self.ErrorLabel.setText("Not a valid input")


app = QApplication(sys.argv)
cheats = CheatsWidget()
widget = QStackedWidget()
widget.addWidget(cheats)
widget.setFixedWidth(1000)
widget.setFixedHeight(600)
widget.show()
try:
    sys.exit(app.exec_())
except:
    print("Exiting")
    sys.exit()
