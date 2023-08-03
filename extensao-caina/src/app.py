# encoding: utf-8
import os
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from core import *

class Application:
    def __init__(self):
        self.__app = QApplication([])
        self.__window = window.MainWindow()

    def Run(self):
        self.__window.show()
        self.__app.exec()

if __name__ == "__main__":
    # Change path to root directory
    os.chdir('..')

    # Create and run application
    app = Application()
    app.Run()