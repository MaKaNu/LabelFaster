import numpy as np
import sys
import os
from pathlib import Path
import shutil

from functools import partial

# PyQT Libraries
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from models import *

from libs.utils import *
from libs.resources import *
from libs.stringBundle import StringBundle
from libs.toolBar import ToolBar
from libs.errors import *

__appname__ = 'ROISA - Region of Interest Selector Automat'


class WindowMixin(object):

    def menu(self, title, actions=None):
        menu = self.menuBar().addMenu(title)
        if actions:
            addActions(menu, actions)
        return menu

    def toolbar(self, title, actions=None):
        toolbar = ToolBar(title)
        toolbar.setObjectName(u'%sToolBar' % title)
        # toolbar.setOrientation(Qt.Vertical)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        if actions:
            addActions(toolbar, actions)
        self.addToolBar(Qt.LeftToolBarArea, toolbar)
        return toolbar


class StartWindow(QMainWindow, WindowMixin):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(__appname__)

        # Load string bundle for i18n
        self.stringBundle = StringBundle.getBundle()

        def getStr(strId):
            return self.stringBundle.getString(strId)

        # Load Model classes

        self.title = 'ROISA - Region of Interest Selector Automat'
        self.left = 1
        self.top = 30
        self.width = 640
        self.height = 480

        self.selectedClass = 0
        self.selectedFolder = '-'
        self.selectedNumIm = '-'
        self.selectedImSize = '-'
        self.selectedstrecth = 'cutting'

        # Actions
        action = partial(newAction, self)
        quit = action(getStr('quit'), self.close,
                      'Ctrl+Q', 'quit', getStr('quitApp'))

        # Store actions for further handling.
        self.actions = loadStruct('action')

        # Create Menus
        self.menus = loadStruct('menu', lambda x: self.menu(x))

        addActions(self.menus.file, (
            quit,
            )
            )
        # addActions(self.menus.help, (help, showInfo))
        # addActions(self.menus.view, (
        #     self.autoSaving,
        #     self.singleClassMode,
        #     self.displayLabelOption,
        #     labels, advancedMode, None,
        #     hideAll, showAll, None,
        #     zoomIn, zoomOut, zoomOrg, None,
        #     fitWindow, fitWidth))

        # Create Toolbars
        self.tools = self.toolbar('Tools')
        self.actions.beginner = (
            quit, quit, quit, None, quit, quit, quit
            )

        addActions(self.tools, self.actions.beginner)

        self.statusBar().showMessage('%s started.' % __appname__)
        self.statusBar().show()


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
    win = StartWindow()
    # win = MainWindow(argv[1] if len(argv) >= 2 else None,
    #                  argv[2] if len(argv) >= 3 else os.path.join(
    #                      os.path.dirname(sys.argv[0]),
    #                      'data', 'predefined_classes.txt'),
    #                  argv[3] if len(argv) >= 4 else None)
    win.show()
    return app, win


def startApp():
    '''construct main app and run it'''
    app, _win = get_main_app(sys.argv)
    return app.exec_()


# For TESTING
if __name__ == '__main__':
    sys.exit(startApp())
