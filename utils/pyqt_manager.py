from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QListWidgetItem


def create_list_widget_item(text, data_dict={}, icon_path=""):
    item = QListWidgetItem(text)
    for data in data_dict.keys():
        item.setData(data, data_dict[data])
    item.setIcon(QIcon(icon_path))
    return item
