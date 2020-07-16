from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from functools import partial
from collections import Counter

from libs.utils import newAction
from libs.stringBundle import StringBundle
from libs.errors import ClassesError

# Load string bundle for i18n
stringBundle = StringBundle.getBundle()


def getStr(strId):
    return stringBundle.getString(strId)


def get_quit(self):
    quit = newAction(
        self,
        getStr('quit'),
        self.close,
        'Ctrl+Q',
        'quit',
        getStr('quitFull'))
    return quit


def get_open(self):
    open = newAction(
        self,
        getStr('file'),
        self.openFile,
        'Ctrl+O',
        'folder',
        getStr('fileFull'))
    return open


def get_startlabel(self):
    startlabel = newAction(
        self,
        getStr('start'),
        self.setCreateMode,
        'G',
        'start',
        getStr('startFull'))
    return startlabel


def create_classes(self):
    classes = self.labelHist
    if len(classes) > 20:
        raise ClassesError(
            classes,
            self.getStr('toomanyclassesE'))
    if any(t > 1 for t in Counter(classes).values()):
        raise ClassesError(
            classes,
            self.getStr('sameclassesE'))
    for classname in classes:
        if classes.index(classname) < 10:
            if classes.index(classname) == 9:
                shortcut = str(0)
            else:
                shortcut = str(classes.index(classname) + 1)
        else:
            if classes.index(classname) == 19:
                shortcut = 'Ctrl+' + str(0)
            else:
                shortcut = 'Ctrl+' + str(classes.index(classname) - 9)
        classvar = newAction(
            self,
            classname,
            self.switchClass,
            shortcut,
            'off',
            'class' + str(classes.index(classname))
        )
        setattr(
            self.classes,
            'class' + str(classes.index(classname)),
            classvar
            )
        setattr(
            self.classes,
            'numClasses',
            len(classes)
        )


def get_classes(self):
    i = 0
    tmplist = []
    for idx in range(self.classes.numClasses):
        classAction = getattr(self.classes, 'class' + str(idx))
        tmplist.append(classAction)
    return tuple(tmplist)
