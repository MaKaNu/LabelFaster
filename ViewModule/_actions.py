from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from functools import partial

from libs.utils import *
from libs.stringBundle import StringBundle

# Load string bundle for i18n
stringBundle = StringBundle.getBundle()


def getStr(strId):
    return stringBundle.getString(strId)


def get_quit(self):
    action = partial(newAction, self)
    quit = action(
        getStr('quit'),
        self.close,
        'Ctrl+Q',
        'quit',
        getStr('quitApp'))
    return quit


def get_open(self):
    action = partial(newAction, self)
    open = action(
        getStr('file'),
        self.openFile,
        'Ctrl+O',
        'folder',
        getStr('openFile'))
    return open
