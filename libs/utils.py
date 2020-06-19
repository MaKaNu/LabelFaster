from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from libs.errors import *


def newIcon(icon):
    return QIcon(':/' + icon)


def newAction(parent, text, slot=None, shortcut=None, icon=None,
              tip=None, checkable=False, enabled=True):
    """Create a new action and assign callbacks, shortcuts, etc."""
    a = QAction(text, parent)
    if icon is not None:
        a.setIcon(newIcon(icon))
    if shortcut is not None:
        if isinstance(shortcut, (list, tuple)):
            a.setShortcuts(shortcut)
        else:
            a.setShortcut(shortcut)
    if tip is not None:
        a.setToolTip(tip)
        a.setStatusTip(tip)
    if slot is not None:
        a.triggered.connect(slot)
    if checkable:
        a.setCheckable(True)
    a.setEnabled(enabled)
    return a


def addActions(widget, actions):
    for action in actions:
        if action is None:
            widget.addSeparator()
        elif isinstance(action, QMenu):
            widget.addMenu(action)
        else:
            widget.addAction(action)


def loadStruct(type, func=None):
    if str(type) == 'action':
        return struct(
            fileMenuActions=(
                quit),
            beginner=(),
            advanced=(),
            editMenu=(),
            beginnerContext=(),
            advancedContext=(),
            onLoadActive=(),
            onShapesPresent=()
            )
    if str(type) == 'menu':
        return struct(
            file=func('&File'),
            edit=func('&Edit'),
            view=func('&View'),
            help=func('&Help'),
            recentFiles=QMenu('Open &Recent')
        )
    else:
        message = 'No struct "' + str(type) + '" included!'
        raise InputError(type, message)


class struct(object):

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
