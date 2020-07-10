from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from functools import partial

from libs.utils import *
from libs.stringBundle import StringBundle
from libs.errors import *

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


def create_classes(self):
    classes = self.labelHist
    action = partial(newAction, self)
    if len(classes) > 20:
        raise ClassesError(classes, self.__getStr('toomanyclassesE'))
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
                shortcut = 'Ctrl+' + str(classes.index(classname) + 1)
        classvar = action(
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
