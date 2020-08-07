#!/usr/bin/env python
# -*- coding: utf-8 -*-
import ctypes
import sys
from pathlib import Path
import os

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from libs.utils import nonePath, newIcon

from ViewModule import StartWindow

__appname__ = 'LF - Label Faster'


def get_main_app(argv=[]):
    """
    Standard boilerplate Qt application code.
    Do everything but app.exec_()
    -- so that we can test the application in one thread
    """
    app = QApplication(argv)
    app.setApplicationName(__appname__)
    app.setWindowIcon(newIcon("logo"))
    # Tzutalin 201705+: Accept extra agruments to change predefined class file
    # Usage : labelImg.py image predefClassFile saveDir
    win = StartWindow(
        __appname__,
        Path(argv[1]) if len(argv) >= 2 else nonePath,
        Path(argv[2]) if len(argv) >= 3 else (
            Path(argv[0]).parent /
            Path('data') /
            Path('predefined_classes.txt')),
        Path(argv[3]) if len(argv) >= 4 else nonePath)
    win.show()
    return app, win


def startApp():
    '''construct main app and run it'''
    app, _win = get_main_app(sys.argv)
    return app.exec_()


if __name__ == '__main__':
    sys.exit(startApp())
