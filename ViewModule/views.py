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

# from models import *

from libs.utils import *
from libs.resources import *
from libs.stringBundle import StringBundle
from libs.toolBar import ToolBar
from libs.canvas import Canvas
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
    def __init__(self, defaultFilename=None):
        super().__init__()
        self.setWindowTitle(__appname__)

        # Standard QT Parameter
        self.title = 'ROISA - Region of Interest Selector Automat'
        self.__left = 1
        self.__top = 30
        self.__width = 640
        self.__height = 480

        # Application state.
        self.__image = QImage()
        self.__filePath = defaultFilename

        # Load string bundle for i18n
        self.__stringBundle = StringBundle.getBundle()
        def getStr(strId): return self.__stringBundle.getString(strId)

        # Load Model classes
        self.__FileWrapper = FileWrapper(
            self,
            self.getPath()
            )

        self.selectedClass = 0
        self.selectedFolder = '-'
        self.selectedNumIm = '-'
        self.selectedImSize = '-'
        self.selectedstrecth = 'cutting'

        # Create Canvas Widget
        self.__canvas = Canvas(parent=self)

        # Actions
        action = partial(newAction, self)

        quit = action(
            getStr('quit'),
            self.close,
            'Ctrl+Q',
            'quit',
            getStr('quitApp'))

        open = action(
            getStr('file'),
            self.__FileWrapper.openFile,
            'Ctrl+O',
            'folder',
            getStr('openFile'))

        class0 = action(
            getStr('class0'),
            self.switchClass,
            'Ctrl+1',
            'class0',
            getStr('class0')

        )

        # Store actions for further handling.
        self.__actions = struct(
            open=open,
            fileMenuActions=(
                open,
                quit),
            beginner=(),
            advanced=(),
            editMenu=(),
            beginnerContext=(),
            advancedContext=(),
            onLoadActive=(),
            onShapesPresent=()
            )

        # Create Menus
        self.__menus = struct(
            file=self.menu('&File'),
            edit=self.menu('&Edit'),
            view=self.menu('&View'),
            help=self.menu('&Help'),
            recentFiles=QMenu('Open &Recent')
            )

        # Fill Menus
        addActions(self.__menus.file, (
            open,
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
        self.__tools = self.toolbar('Tools')
        self.__actions.beginner = (
            open, None, quit
            )

        addActions(self.__tools, self.__actions.beginner)

        self.statusBar().showMessage('%s started.' % __appname__)
        self.statusBar().show()

    def adjustScale(self, initial=False):
        value = self.scalers[self.FIT_WINDOW if initial else self.zoomMode]()
        self.zoomWidget.setValue(int(100 * value))

    ###########################################################################
    #                               G E T T E R                               #
    ###########################################################################

    def getPath(self):
        return self.__filePath

    ###########################################################################
    #                               S E T T E R                               #
    ###########################################################################


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
