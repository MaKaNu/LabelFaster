from os import DirEntry
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
from libs.shape import Shape, DEFAULT_LINE_COLOR, DEFAULT_FILL_COLOR
from libs.zoomWidget import ZoomWidget
from libs.settings import Settings
from libs.errors import *
from libs.labelFile import LabelFile
from libs.yolo_io import TXT_EXT
from libs.pascal_io import XML_EXT
from libs.boxsup_io import PNG_EXT


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

        # Unsaved Status Flag
        self.__dirty = False

        # For loading all image under a directory
        self.__mImgList = []
        self.__foldername = None
        self.__labelHist = []

        # Match Shapes and Labels
        self.__itemsToShapes = {}
        self.__shapesToItems = {}
        self.__prevLabelText = ''

        # Application state.
        self.__selectedClass = None

        # File and path informations
        self.__image = QImage()
        self.__filePath = defaultFilename
        self.__defaultSaveDir = defaultSaveDir
        self.__lastOpenFolder = None
        self.__loadPredefinedClasses(defaultPredefClassFile)

        # Application state
        self.__lineColor = None
        self.__fillColor = None

        # Load string bundle for i18n
        self.__stringBundle = StringBundle.getBundle()
        def getStr(strId): return self.__stringBundle.getString(strId)

        # Save as Format Flags
        self.__defaultSaveDir = defaultSaveDir
        self.__usePascalVocFormat = True
        self.__useYoloFormat = False
        self.__useBoxSupFormat = False

        # ##############################WDIGETS############################## #

        # Create ZoomWidget
        self.zoomWidget = ZoomWidget()

        # ____________________    __________       _____
        # ___  ____/__(_)__  /_______  /__(_)________  /_
        # __  /_   __  /__  /_  _ \_  /__  /__  ___/  __/
        # _  __/   _  / _  / /  __/  / _  / _(__  )/ /_
        # /_/      /_/  /_/  \___//_/  /_/  /____/ \__/

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

        self.__fileListWidget = QListWidget()
        self.fileListWidget.itemDoubleClicked.\
            connect(self.fileitemDoubleClicked)
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

        # ____________                      ______
        # __  ___/__(_)______ _____________ ___  /_______
        # _____ \__  /__  __ `/_  __ \  __ `/_  /__  ___/
        # ____/ /_  / _  /_/ /_  / / / /_/ /_  / _(__  )
        # /____/ /_/  _\__, / /_/ /_/\__,_/ /_/  /____/

        self.canvas.newShape.connect(self.newShape)

        self.setCentralWidget(scroll)
        self.addDockWidget(Qt.RightDockWidgetArea, self.boxDock)
        self.addDockWidget(Qt.RightDockWidgetArea, self.fileDock)
        self.fileDock.setFeatures(QDockWidget.DockWidgetFloatable)

        self.dockFeatures = QDockWidget.DockWidgetClosable \
            | QDockWidget.DockWidgetFloatable
        self.boxDock.setFeatures(self.boxDock.features() ^ self.dockFeatures)

        # _______      __________
        # ___    |_______  /___(_)____________________
        # __  /| |  ___/  __/_  /_  __ \_  __ \_  ___/
        # _  ___ / /__ / /_ _  / / /_/ /  / / /(__  )
        # /_/  |_\___/ \__/ /_/  \____//_/ /_//____/

        # Load Actions

        # Manage File system
        quit = self.get_quit()
        open = self.get_open()
        openfolder = self.get_openfolder()
        start = self.get_startlabel()
        save = self.get_save()
        changesavefolder = self.get_changesavefolder()
        autosaving = self.get_autosaving()
        saveformat = self.get_saveformat()

        # Manage Window Zoom
        zoom = self.get_zoom()
        zoomIn = self.get_zoomin()
        zoomOut = self.get_zoomout()
        zoomOrg = self.get_zoomorg()
        fitWindow = self.get_fitwindow()
        fitWidth = self.get_fitwidth()

        # Store actions for further handling.
        self.__actions = struct(
            open=open, openfolder=openfolder, quit=quit, zoom=zoom,
            zoomIn=zoomIn, zoomOut=zoomOut, zoomOrg=zoomOrg,
            start=start, fitWindow=fitWindow, fitWidth=fitWidth,
            autosaving=autosaving, save=save, saveformat=saveformat,
            changesavefolder=changesavefolder,
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
            onShapesPresent=(),
            zoomActions=(
                self.zoomWidget, zoomIn, zoomOut, zoomOrg, fitWindow, fitWidth)
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
            openfolder,
            changesavefolder,
            save,
            saveformat,
            autosaving,
            quit,
        ))
        addActions(self.menus.edit, (
            start,
        ))
        addActions(self.menus.view, (
            zoomIn, zoomOut, zoomOrg, None, fitWindow, fitWidth
        ))
        # self.autoSaving,
        # self.singleClassMode,
        # self.displayLabelOption,
        # labels, advancedMode, None,
        # hideAll, showAll, None,
        # zoomIn, zoomOut, zoomOrg, None,
        # addActions(self.menus.help, (help, showInfo))

        # Create Toolbars
        self.tools = self.toolbar('Tools', position='left')
        self.classtools = self.toolbar('Classes', position='top')
        self.actions.beginner = (
            open, openfolder, saveformat, None, start,
            None, zoomIn, zoom, zoomOrg, zoomOut, fitWindow,
            fitWidth, None,  quit
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

        Shape.line_color = self.lineColor = QColor(
            settings.get(SETTING_LINE_COLOR, DEFAULT_LINE_COLOR))
        Shape.fill_color = self.fillColor = QColor(
            settings.get(SETTING_FILL_COLOR, DEFAULT_FILL_COLOR))
        self.canvas.setDrawingColor(self.lineColor)

        self.zoomWidget.valueChanged.connect(self.paintCanvas)

    ###########################################################################
    #                       I M P O R T   M E T H O D S                       #
    ###########################################################################

    from ._actions import get_open, get_openfolder, get_quit, create_classes, \
        get_classes, get_startlabel, get_zoom,  get_zoomin, get_zoomout, \
        get_zoomorg, get_fitwindow, get_fitwidth, get_autosaving, get_save, \
        get_changesavefolder, get_saveformat
    from ._filehandler import openFile, openFolder, loadFile, mayContinue, \
        importFolderImgs, scanAllImages, openPrevImg, openNextImg, \
        fileitemDoubleClicked, saveFile, changeSaveFolderDialog,\
        selectSaveFile, saveFileDialog, currentPath, saveLabels
    from ._label import addLabel
    from ._events import status

    ###########################################################################
    #                        A C T I O N M E T H O D S                        #
    ###########################################################################
    def setCreateMode(self):
        self.toggleDrawMode(False)

    def setZoom(self, value):
        self.actions.fitWidth.setChecked(False)
        self.actions.fitWindow.setChecked(False)
        self.zoomMode = self.MANUAL_ZOOM
        self.zoomWidget.setValue(value)

    def addZoom(self, increment=10):
        self.setZoom(self.zoomWidget.value() + increment)

    def setFitWindow(self, value=True):
        if value:
            self.actions.fitWidth.setChecked(False)
        self.zoomMode = self.FIT_WINDOW if value else self.MANUAL_ZOOM
        self.adjustScale()

    def setFitWidth(self, value=True):
        if value:
            self.actions.fitWindow.setChecked(False)
        self.zoomMode = self.FIT_WIDTH if value else self.MANUAL_ZOOM
        self.adjustScale()

    def changeFormat(self):
        if self.usePascalVocFormat:
            self.set_format(FORMAT_YOLO)
        elif self.useYoloFormat:
            self.set_format(FORMAT_BOXSUP)
        elif self.useBoxSupFormat:
            self.set_format(FORMAT_PASCALVOC)

    def switchClass(self):
        name = self.sender().toolTip()
        self.selectedClass = self.sender().text()
        getattr(self.classes, name).setIcon(newIcon('green'))
        if (
                self.classes.activeClass is not None and
                not self.classes.activeClass == name):
            getattr(
                self.classes,
                self.classes.activeClass
                ).setIcon(newIcon('red'))
        setattr(self.classes, 'activeClass', name)

    ###########################################################################
    #                        S I G N A L M E T H O D S                        #
    ###########################################################################

    def newShape(self):
        if self.selectedClass is not None:
            text = self.selectedClass
            self.prevLabelText = text
            generate_color = generateColorByText(text)
            shape = self.canvas.setLastLabel(
                text,
                generate_color,
                generate_color)
            self.addLabel(shape)
            # if self.beginner():  # Switch to edit mode.
            #     self.canvas.setEditing(True)
            #     self.actions.create.setEnabled(True)
            # else:
            #     self.actions.editMode.setEnabled(True)
            self.dirty = True

            if text not in self.labelHist:
                self.labelHist.append(text)
        else:
            self.canvas.resetAllLines()

    ###########################################################################
    #                              M E T H O D S                              #
    ###########################################################################

    def resetState(self):
        self.itemsToShapes.clear()
        self.shapesToItems.clear()
        self.labelList.clear()
        self.filePath = None
        self.imageData = None
        self.labelFile = None
        self.canvas.resetState()
        self.labelCoordinates.clear()

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

    def __loadPredefinedClasses(self, predefClassesFile):
        if Path(predefClassesFile).exists():
            with codecs.open(predefClassesFile, 'r', 'utf8') as f:
                for line in f:
                    line = line.strip()
                    if self.labelHist is None:
                        self.labelHist = [line]
                    else:
                        self.labelHist.append(line)

    def toggleDrawMode(self, edit=True):
        self.canvas.setEditing(edit)

    def toggleActions(self, value=True):
        """Enable/Disable widgets which depend on an opened image."""
        for z in self.actions.zoomActions:
            if z is not None:
                z.setEnabled(value)
        # for action in self.actions.onLoadActive:
        #     action.setEnabled(value)

    def set_format(self, save_format):
        if save_format == FORMAT_PASCALVOC:
            self.actions.saveformat.setText(FORMAT_PASCALVOC)
            self.actions.saveformat.setIcon(newIcon("format_voc"))
            self.usePascalVocFormat = True
            self.useYoloFormat = False
            self.useBoxSupFormat = False
            LabelFile.suffix = XML_EXT

        elif save_format == FORMAT_YOLO:
            self.actions.saveformat.setText(FORMAT_YOLO)
            self.actions.saveformat.setIcon(newIcon("format_yolo"))
            self.usePascalVocFormat = False
            self.useYoloFormat = True
            self.useBoxSupFormat = False
            LabelFile.suffix = TXT_EXT

        elif save_format == FORMAT_BOXSUP:
            self.actions.saveformat.setText(FORMAT_BOXSUP)
            self.actions.saveformat.setIcon(newIcon("format_boxsup"))
            self.usePascalVocFormat = False
            self.useYoloFormat = False
            self.useBoxSupFormat = True
            LabelFile.suffix = PNG_EXT

    ###########################################################################
    #                               G E T T E R                               #
    ###########################################################################
    def __getActions(self):
        return self.__actions

    def __getFilePath(self):
        return self.__filePath

    def __getAppname(self):
        return self.__appname

    def __getCanvas(self):
        return self.__canvas

    def __getDefaultSaveDir(self):
        return self.__defaultSaveDir

    def __getImage(self):
        return self.__image

    def __getStr(self, strId):
        return self.__stringBundle.getString(strId)

    def __getSelectedClass(self):
        return self.__selectedClass

    def __getItemsToShapes(self):
        return self.__itemsToShapes

    def __getShapesToItems(self):
        return self.__shapesToItems

    def __getPrevLabelText(self):
        return self.__prevLabelText

    def __getDirty(self):
        return self.__dirty

    def __getLastOpenFolder(self):
        return self.__lastOpenFolder

    def __getMImgList(self):
        return self.__mImgList

    def __getFoldername(self):
        return self.__foldername

    def __getLabelHist(self):
        return self.__labelHist

    def __getFileListWidget(self):
        return self.__fileListWidget

    def __getDefaultSaveDir(self):
        return self.__defaultSaveDir

    def __getUPascalVocFormat(self):
        return self.__usePascalVocFormat

    def __getUYoloFormat(self):
        return self.__useYoloFormat

    def __getUBoxSupFormat(self):
        return self.__useBoxSupFormat

    def __getLineColor(self):
        return self.__lineColor

    def __getFillColor(self):
        return self.__fillColor

    ###########################################################################
    #                               S E T T E R                               #
    ###########################################################################
    def __setActions(self, x):
        if isinstance(x, struct):
            self.__actions = x
        else:
            raise ValueError(x, self.__getStr('structE'))

    def __setFilePath(self, x):
        if isinstance(x, str) or x is None:
            self.__filePath = x
        else:
            raise ValueError(x, self.__getStr('pathE'))

    def __setDefaultSaveDir(self, x):
        if isinstance(x, str) or x is None:
            self.__defaultSaveDir = x
        else:
            raise ValueError(x, self.__getStr('pathE'))

    def __setDirty(self, x):
        if isinstance(x, bool):
            self.__dirty = x
            if x:
                self.actions.save.setEnabled(True)
            else:
                self.actions.save.setEnabled(False)
                self.actions.start.setEnabled(True)
        else:
            raise ValueError(x, self.__getStr('boolE'))

    def __setImage(self, x):
        self.__image = x

    def __setImage(self, x):
        if isinstance(x, QImage) or x is None:
            self.__image = x
        else:
            raise ValueError(x, self.__getStr('imageE'))

    def __setSelectedClass(self, x):
        if isinstance(x, str):
            self.__selectedClass = x
        else:
            raise ValueError(x, self.__getStr('strE'))

    def __setItemsToShapes(self, x):
        if isinstance(x, dict):
            self.__itemsToShapes = x
        else:
            raise ValueError(x, self.__getStr('dictE'))

    def __setShapesToItems(self, x):
        if isinstance(x, dict):
            self.__shapesToItems = x
        else:
            raise ValueError(x, self.__getStr('dictE'))

    def __setPrevLabelText(self, x):
        if isinstance(x, str):
            self.__prevLabelText = x
        else:
            raise ValueError(x, self.__getStr('strE'))

    def __setLastOpenFolder(self, x):
        if isinstance(x, str) or x is None:
            self.__lastOpenFolder = x
        else:
            raise ValueError(x, self.__getStr('pathE'))

    def __setMImgList(self, x):
        if isinstance(x, list):
            self.__mImgList = x
        else:
            raise ValueError(x, self.__getStr('listE'))

    def __setFoldername(self, x):
        if isinstance(x, str):
            self.__foldername = x
        else:
            raise ValueError(x, self.__getStr('strE'))

    def __setLabelHist(self, x):
        if isinstance(x, list):
            self.__labelHist = x
        else:
            raise ValueError(x, self.__getStr('listE'))

    def __setFileListWidget(self, x):
        if isinstance(x, QListWidget):
            self.__fileListWidget = x
        else:
            raise ValueError(x, self.__getStr('qlistwidgetE'))

    def __setDefaultSaveDir(self, x):
        if isinstance(x, str) or x is None:
            self.__defaultSaveDir = x
        else:
            raise ValueError(x, self.__getStr('strE'))

    def __setUPascalVocFormat(self, x):
        if isinstance(x, bool):
            self.__usePascalVocFormat = x
        else:
            raise ValueError(x, self.__getStr('boolE'))

    def __setUYoloFormat(self, x):
        if isinstance(x, bool):
            self.__useYoloFormat = x
        else:
            raise ValueError(x, self.__getStr('boolE'))

    def __setUBoxSupFormat(self, x):
        if isinstance(x, bool):
            self.__useBoxSupFormat = x
        else:
            raise ValueError(x, self.__getStr('boolE'))

    def __setLineColor(self, x):
        if isinstance(x, QColor):
            self.__lineColor = x
        else:
            raise ValueError(x, self.__getStr('qcolorE'))

    def __setFillColor(self, x):
        if isinstance(x, QColor):
            self.__fillColor = x
        else:
            raise ValueError(x, self.__getStr('qcolorE'))

    ###########################################################################
    #                           P R O P E R T I E S                           #
    ###########################################################################

    actions = property(__getActions, __setActions)
    filePath = property(__getFilePath, __setFilePath)
    appname = property(__getAppname)
    canvas = property(__getCanvas)
    image = property(__getImage, __setImage)
    defaultSaveDir = property(__getDefaultSaveDir, __setDefaultSaveDir)
    selectedClass = property(__getSelectedClass, __setSelectedClass)
    itemsToShapes = property(__getItemsToShapes, __setItemsToShapes)
    shapesToItems = property(__getShapesToItems, __setShapesToItems)
    prevLabelText = property(__getPrevLabelText, __setPrevLabelText)
    dirty = property(__getDirty, __setDirty)
    lastOpenFolder = property(__getLastOpenFolder, __setLastOpenFolder)
    mImgList = property(__getMImgList, __setMImgList)
    foldername = property(__getFoldername, __setFoldername)
    labelHist = property(__getLabelHist, __setLabelHist)
    fileListWidget = property(__getFileListWidget, __setFileListWidget)
    defaultSaveDir = property(__getDefaultSaveDir, __setDefaultSaveDir)
    usePascalVocFormat = property(__getUPascalVocFormat, __setUPascalVocFormat)
    useYoloFormat = property(__getUYoloFormat, __setUYoloFormat)
    useBoxSupFormat = property(__getUBoxSupFormat, __setUBoxSupFormat)
    lineColor = property(__getLineColor, __setLineColor)
    fillColor = property(__getFillColor, __setFillColor)
