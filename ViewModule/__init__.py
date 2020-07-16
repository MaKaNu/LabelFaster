from pathlib import Path
import codecs

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from libs.utils import *
from libs.resources import *
from libs.constants import *
from libs.stringBundle import StringBundle
from libs.toolBar import ToolBar
from libs.canvas import Canvas
from libs.zoomWidget import ZoomWidget
from libs.settings import Settings
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

        # Load setting in the main thread
        self.settings = Settings()
        self.settings.load()
        settings = self.settings

        # Standard QT Parameter
        self.title = 'ROISA - Region of Interest Selector Automat'

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

        # ____   ___ ___ _    ___ _    ___ ___ _____    _____
        #    /  | __|_ _| |  | __| |  |_ _/ __|_   _|  /     \
        #   /   | _| | || |__| _|| |__ | |\__ \ | |   /       \
        # __\   |_| |___|____|___|____|___|___/ |_|   \_______/

        # Create FileListWidget
        listLayout = QVBoxLayout()
        listLayout.setContentsMargins(0, 0, 0, 0)

        # Create and add a widget for showing current label items
        self.labelList = QListWidget()
        labelListContainer = QWidget()
        labelListContainer.setLayout(listLayout)
        # self.labelList.itemActivated.connect(self.labelSelectionChanged)
        # self.labelList.itemSelectionChanged.connect(self.labelSelectionChanged)
        # self.labelList.itemDoubleClicked.connect(self.editLabel)
        # Connect to itemChanged to detect checkbox changes.
        # self.labelList.itemChanged.connect(self.labelItemChanged)
        listLayout.addWidget(self.labelList)

        self.boxDock = QDockWidget(getStr('boxLabelText'), self)
        self.boxDock.setObjectName(getStr('labels'))
        self.boxDock.setWidget(labelListContainer)

        self.fileListWidget = QListWidget()
        # self.fileListWidget.itemDoubleClicked.connect(self.fileitemDoubleClicked)
        filelistLayout = QVBoxLayout()
        filelistLayout.setContentsMargins(0, 0, 0, 0)
        filelistLayout.addWidget(self.fileListWidget)
        fileListContainer = QWidget()
        fileListContainer.setLayout(filelistLayout)
        self.fileDock = QDockWidget(getStr('fileList'), self)
        self.fileDock.setObjectName(getStr('files'))
        self.fileDock.setWidget(fileListContainer)

        # Create Canvas Widget
        self.__canvas = Canvas(parent=self)
        self.canvas.setEnabled(False)

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
        self.addDockWidget(Qt.RightDockWidgetArea, self.boxDock)
        self.addDockWidget(Qt.RightDockWidgetArea, self.fileDock)
        self.fileDock.setFeatures(QDockWidget.DockWidgetFloatable)

        self.dockFeatures = QDockWidget.DockWidgetClosable \
            | QDockWidget.DockWidgetFloatable
        self.boxDock.setFeatures(self.boxDock.features() ^ self.dockFeatures)

        # ____    _   ___ _____ ___ ___  _  _ ___     _____
        #    /   /_\ / __|_   _|_ _/ _ \| \| / __|   /     \
        #   /   / _ \ (__  | |  | | (_) | .` \__ \  /       \
        # __\  /_/ \_\___| |_| |___\___/|_|\_|___/  \_______/

        # Load Actions
        quit = self.get_quit()
        open = self.get_open()
        start = self.get_startlabel()

        # Store actions for further handling.
        self.actions = struct(
            quit=quit,
            open=open,
            start=start,
            fileMenuActions=(
                open,
                quit),
            beginner=(),
            advanced=(),
            classes=(),
            editMenu=(
                start,),
            beginnerContext=(),
            advancedContext=(),
            onLoadActive=(),
            onShapesPresent=()
            )

        # Store class Actions
        self.classes = struct(
            activeClass=None
            )
        self.create_classes()

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
        ))
        addActions(self.menus.edit, (
            start,
        ))
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
        self.tools = self.toolbar('Tools', position='left')
        self.classtools = self.toolbar('Classes', position='top')
        self.actions.beginner = (
            open, None, start, quit
            )

        self.actions.classes = self.get_classes()

        addActions(self.tools, self.actions.beginner)
        addActions(self.classtools, self.actions.classes)

        self.statusBar().showMessage('%s started.' % appname)
        self.statusBar().show()

        self.zoomMode = self.MANUAL_ZOOM
        self.scalers = {
            self.FIT_WINDOW: self.scaleFitWindow,
            self.FIT_WIDTH: self.scaleFitWidth,
            # Set to one to scale to 100% when loading files.
            self.MANUAL_ZOOM: lambda: 1,
        }

        # Display cursor coordinates at the right of status bar
        self.labelCoordinates = QLabel('')
        self.statusBar().addPermanentWidget(self.labelCoordinates)

        # Resize and Position Application
        size = settings.get(SETTING_WIN_SIZE, QSize(600, 500))
        position = QPoint(0, 0)
        saved_position = settings.get(SETTING_WIN_POSE, position)
        for i in range(QApplication.desktop().screenCount()):
            desktop = QApplication.desktop().availableGeometry(i)
            if desktop.contains(saved_position):
                position = saved_position
                break
        self.resize(size)
        self.move(position)

    ###########################################################################
    #                       I M P O R T   M E T H O D S                       #
    ###########################################################################

    from ._actions import get_open, get_quit, create_classes, get_classes
    from ._filehandler import openFile, loadFile
    from ._events import status

    ###########################################################################
    #                              M E T H O D S                              #
    ###########################################################################

    def adjustScale(self, initial=False):
        value = self.scalers[self.FIT_WINDOW if initial else self.zoomMode]()
        self.zoomWidget.setValue(int(100 * value))

    def resizeEvent(self, event):
        if self.canvas and not self.image.isNull()\
           and self.zoomMode != self.MANUAL_ZOOM:
            self.adjustScale()
        super(StartWindow, self).resizeEvent(event)

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
        name = self.sender().toolTip()
        getattr(self.classes, name).setIcon(newIcon('green'))
        if (
                self.classes.activeClass is not None and
                not self.classes.activeClass == name):
            getattr(
                self.classes,
                self.classes.activeClass
                ).setIcon(newIcon('red'))
        setattr(self.classes, 'activeClass', name)

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

    def __getImage(self):
        return self.__image

    def getStr(self, strId):
        return self.__stringBundle.getString(strId)
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

    def __setImage(self, x):
        self.__image = x

    ###########################################################################
    #                           P R O P E R T I E S                           #
    ###########################################################################

    path = property(__getPath)
    appname = property(__getAppname)
    canvas = property(__getCanvas)
    image = property(__getImage, __setImage)
    defaultSaveDir = property(__getDefaultSaveDir, __setDefaultSaveDir)
