from pathlib import Path
import codecs

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from libs.utils import *
from libs.resources import *
from libs.stringBundle import StringBundle
from libs.toolBar import ToolBar
from libs.canvas import Canvas
from libs.zoomWidget import ZoomWidget
from libs.errors import *


class WindowMixin(object):

    def menu(self, title, actions=None):
        menu = self.menuBar().addMenu(title)
        if actions:
            addActions(menu, actions)
        return menu

    def toolbar(self, title, actions=None, position='left'):
        toolbar = ToolBar(title)
        toolbar.setObjectName(u'%sToolBar' % title)
        # toolbar.setOrientation(Qt.Vertical)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        if actions:
            addActions(toolbar, actions)
        if position == 'left':
            self.addToolBar(Qt.LeftToolBarArea, toolbar)
        elif position == 'top':
            self.addToolBar(Qt.TopToolBarArea, toolbar)
        return toolbar


class StartWindow(QMainWindow, WindowMixin):
    FIT_WINDOW, FIT_WIDTH, MANUAL_ZOOM = list(range(3))

    def __init__(
            self,
            appname='defaultName',
            defaultFilename=None,
            defaultPredefClassFile=None,
            defaultSaveDir=None):
        super().__init__()
        self.__appname = appname
        self.setWindowTitle(appname)

        # Standard QT Parameter
        self.title = 'ROISA - Region of Interest Selector Automat'
        self.__left = 1
        self.__top = 30
        self.__width = 640
        self.__height = 480

        # For loading all image under a directory
        self.mImgList = []
        self.dirname = None
        self.labelHist = []
        self.lastOpenDir = None

        # Application state.
        self.__image = QImage()
        self.__filePath = defaultFilename
        self.__loadPredefinedClasses(defaultPredefClassFile)

        # Load string bundle for i18n
        self.__stringBundle = StringBundle.getBundle()
        def getStr(strId): return self.__stringBundle.getString(strId)

        # Save as Pascal voc xml
        self.__defaultSaveDir = defaultSaveDir
        # self.usingPascalVocFormat = True
        # self.usingYoloFormat = False

        # ##############################WDIGETS############################## #

        # Create ZoomWidget
        self.zoomWidget = ZoomWidget()

        # Create Canvas Widget
        self.__canvas = Canvas(parent=self)

        # Create Central Widget
        scroll = QScrollArea()
        scroll.setWidget(self.canvas)
        scroll.setWidgetResizable(True)
        self.scrollBars = {
            Qt.Vertical: scroll.verticalScrollBar(),
            Qt.Horizontal: scroll.horizontalScrollBar()
        }
        self.scrollArea = scroll

        self.setCentralWidget(scroll)

        # Load Actions
        quit = self.get_quit()
        open = self.get_open()
        class0 = self.get_class0()

        # Store actions for further handling.
        self.__actions = struct(
            open=open,
            class0=class0,
            fileMenuActions=(
                open,
                quit),
            beginner=(),
            advanced=(),
            classes=(),
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
        self.__tools = self.toolbar('Tools', position='left')
        self.__classes = self.toolbar('Classes', position='top')
        self.__actions.beginner = (
            open, None, quit
            )
        self.__actions.classes = (
            class0, class0
            )

        addActions(self.__tools, self.__actions.beginner)
        addActions(self.__classes, self.__actions.classes)

        self.statusBar().showMessage('%s started.' % appname)
        self.statusBar().show()

        self.scalers = {
            self.FIT_WINDOW: self.scaleFitWindow,
            self.FIT_WIDTH: self.scaleFitWidth,
            # Set to one to scale to 100% when loading files.
            self.MANUAL_ZOOM: lambda: 1,
        }

    ###########################################################################
    #                       I M P O R T   M E T H O D S                       #
    ###########################################################################

    from ._actions import get_open, get_quit, get_class0
    from ._filehandler import openFile, loadFile
    from ._events import status

    ###########################################################################
    #                              M E T H O D S                              #
    ###########################################################################

    def adjustScale(self, initial=False):
        value = self.scalers[self.FIT_WINDOW if initial else self.zoomMode]()
        self.zoomWidget.setValue(int(100 * value))

    def scaleFitWindow(self):
        # Figure out the size of the pixmap in order to fit the main widget.
        e = 2.0  # So that no scrollbars are generated.
        w1 = self.centralWidget().width() - e
        h1 = self.centralWidget().height() - e
        a1 = w1 / h1
        # Calculate a new scale value based on the pixmap's aspect ratio.
        w2 = self.canvas.pixmap.width() - 0.0
        h2 = self.canvas.pixmap.height() - 0.0
        a2 = w2 / h2
        return w1 / w2 if a2 >= a1 else h1 / h2

    def scaleFitWidth(self):
        # The epsilon does not seem to work too well here.
        w = self.centralWidget().width() - 2.0
        return w / self.canvas.pixmap.width()

    def paintCanvas(self):
        assert not self.image.isNull(), "cannot paint null image"
        self.canvas.scale = 0.01 * self.zoomWidget.value()
        self.canvas.adjustSize()
        self.canvas.update()

    def switchClass(self):
        action = self.__actions.class0
        action.setIcon(newIcon('red'))
        self.__actions.class0 = action

    def __loadPredefinedClasses(self, predefClassesFile):
        if Path(predefClassesFile).exists():
            with codecs.open(predefClassesFile, 'r', 'utf8') as f:
                for line in f:
                    line = line.strip()
                    if self.labelHist is None:
                        self.labelHist = [line]
                    else:
                        self.labelHist.append(line)

    ###########################################################################
    #                               G E T T E R                               #
    ###########################################################################

    def __getPath(self):
        return self.__filePath

    def __getAppname(self):
        return self.__appname

    def __getCanvas(self):
        return self.__canvas

    def __getDefaultSaveDir(self):
        return self.__defaultSaveDir

    ###########################################################################
    #                               S E T T E R                               #
    ###########################################################################

    def __setDefaultSaveDir(self, x):
        self.__defaultSaveDir = x

    def setDirty(self):
        self.__dirty = True
        # self.actions.save.setEnabled(True)

    def setClean(self):
        self.__dirty = False
        # self.__actions.save.setEnabled(False)
        # self.__actions.create.setEnabled(True)

    ###########################################################################
    #                           P R O P E R T I E S                           #
    ###########################################################################

    path = property(__getPath)
    appname = property(__getAppname)
    canvas = property(__getCanvas)
    defaultSaveDir = property(__getDefaultSaveDir, __setDefaultSaveDir)
