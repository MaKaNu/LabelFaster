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
    def __init__(self, defaultFilename=None):
        super().__init__()
        self.setWindowTitle(__appname__)

        # Standard QT Parameter
        self.title = 'ROISA - Region of Interest Selector Automat'
        self.left = 1
        self.top = 30
        self.width = 640
        self.height = 480

        # Application state.
        self.image = QImage()
        self.filePath = defaultFilename

        # Load string bundle for i18n
        self.stringBundle = StringBundle.getBundle()

        def getStr(strId):
            return self.stringBundle.getString(strId)

        # Load Model classes
        # self.FileWrapper = FileWrapper(self)

        self.selectedClass = 0
        self.selectedFolder = '-'
        self.selectedNumIm = '-'
        self.selectedImSize = '-'
        self.selectedstrecth = 'cutting'

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
            FileWrapper.openFile(),
            'Ctrl+O',
            'folder',
            getStr('openFile'))

        # Store actions for further handling.
        self.actions = struct(
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
        self.menus = struct(
            file=self.menu('&File'),
            edit=self.menu('&Edit'),
            view=self.menu('&View'),
            help=self.menu('&Help'),
            recentFiles=QMenu('Open &Recent')
            )

        # Fill Menus
        addActions(self.menus.file, (
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
        self.tools = self.toolbar('Tools')
        self.actions.beginner = (
            open, None, quit
            )

        addActions(self.tools, self.actions.beginner)

        self.statusBar().showMessage('%s started.' % __appname__)
        self.statusBar().show()

    # def openFile(self):
    #     path = os.path.dirname(self.filePath) if self.filePath else '.'
    #     formats = [
    #         '*.%s' % fmt.data().decode("ascii").lower()
    #         for fmt in QImageReader.supportedImageFormats()]
    #     filters = "Image & Label files (%s)" % ' '.join(
    #         formats +
    #         ['*%s' % LabelFile.suffix])
    #     filename = QFileDialog.getOpenFileName(
    #         self,
    #         '%s - Choose Image or Label file' % __appname__, path, filters)
    #     if filename:
    #         if isinstance(filename, (tuple, list)):
    #             filename = filename[0]
    #         self.loadFile(filename)


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
