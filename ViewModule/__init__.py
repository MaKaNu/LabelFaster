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
            defaultFilename=nonePath,
            defaultPredefClassFile=nonePath,
            defaultImageFolder=nonePath,
            defaultLabelFolder=nonePath):
        super().__init__()
        self.__appname = appname
        self.setWindowTitle(appname)

        # Load string bundle for i18n
        self.__stringBundle = StringBundle.getBundle()
        def getStr(strId): return self.__stringBundle.getString(strId)

        # Load setting in the main thread
        self.settings = Settings()
        self.settings.load()
        settings = self.settings

        # Unsaved Status Flag
        self.__dirty = False

        # For loading all image under a directory
        self.__mImgList = []
        self.__foldername = nonePath
        self.__labelHist = []

        # Match Shapes and Labels
        self.__itemsToShapes = {}
        self.__shapesToItems = {}
        self.__prevLabelText = ''
        self.__noSelectionSlot = False

        # Application state.
        self.__selectedClass = None

        # File and path informations
        self.__image = QImage()
        self.__filePath = defaultFilename
        self.__imageFolder = defaultImageFolder
        self.__labelFolder = defaultLabelFolder
        self.__lastOpenFolder = nonePath
        self.__loadPredefinedClasses(defaultPredefClassFile)
        self.__recentFiles = []
        self.__maxRecent = 7

        # Application state
        self.__lineColor = None
        self.__fillColor = None

        # Save as Format Flags
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
        self.labelList.itemActivated.connect(self.labelSelectionChanged)
        self.labelList.itemSelectionChanged.connect(self.labelSelectionChanged)
        # self.labelList.itemDoubleClicked.connect(self.editLabel)
        # Connect to itemChanged to detect checkbox changes.
        self.labelList.itemChanged.connect(self.labelItemChanged)
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
        self.canvas.shapeMoved.connect(self.shapeMoved)
        self.canvas.selectionChanged.connect(self.shapeSelectionChanged)

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
        openNextImg = self.get_openNextImg()
        openPrevImg = self.get_openPrevImg()

        # Load Settings
        autosaving.setChecked(settings.get(SETTING_AUTO_SAVE, False))
        if settings.get(SETTING_RECENT_FILES):
            self.recentFiles = settings.get(SETTING_RECENT_FILES)

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
            changesavefolder=changesavefolder, openNextImg=openNextImg,
            openPrevImg=openPrevImg,
            fileMenuActions=(
                open,
                openfolder,
                start,
                quit),
            beginner=(),
            advanced=(),
            classes=(),
            editMenu=(
                start,),
            beginnerContext=(),
            advancedContext=(),
            onLoadActive=(start, ),
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
            self.menus.recentFiles,
            save,
            saveformat,
            autosaving,
            openNextImg,
            openPrevImg,
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

        self.menus.file.aboutToShow.connect(self.updateFileMenu)

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
        size = settings.get(SETTING_WIN_SIZE, QSize(820, 800))
        position = QPoint(0, 0)
        saved_position = settings.get(SETTING_WIN_POSE, position)
        for i in range(QApplication.desktop().screenCount()):
            desktop = QApplication.desktop().availableGeometry(i)
            if desktop.contains(saved_position):
                position = saved_position
                break
        self.resize(size)
        self.move(position)

        # Load Default Save settings
        LabelDir = settings.get(SETTING_LABEL_DIR, nonePath)
        if LabelDir is None:
            LabelDir = nonePath  # TODO make nonePath pickable
        TemplastOpenFolder = settings.get(SETTING_LAST_OPEN_FOLDER, nonePath)
        if TemplastOpenFolder is None:
            self.lastOpenFolder = nonePath  # TODO make nonePath picklable
        else:
            self.lastOpenFolder = TemplastOpenFolder
        if self.labelFolder is nonePath and LabelDir is not nonePath and \
                LabelDir.exists():
            self.labelFolder = LabelDir
            self.statusBar().showMessage(
                '%s started. Annotation will be saved to %s' %
                (self.appname, self.labelFolder))
            self.statusBar().show()

        self.restoreState(settings.get(SETTING_WIN_STATE, QByteArray()))

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
        get_changesavefolder, get_saveformat, get_openNextImg, get_openPrevImg
    from ._filehandler import openFile, openFolder, loadFile, mayContinue, \
        importFolderImgs, scanAllImages, openPrevImg, openNextImg, \
        fileitemDoubleClicked, saveFile, changeSaveFolderDialog, \
        initiateSaveProcess, saveFileDialog, currentPath, saveLabels, \
        loadPascalXMLByFilename, loadYOLOTXTByFilename, \
        createLabelFolderFile, addRecentFile, loadRecent, updateFileMenu
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

    def shapeMoved(self):
        self.dirty = True

    def shapeSelectionChanged(self, selected=False):
        if self.noSelectionSlot:
            self.noSelectionSlot = False
        else:
            shape = self.canvas.selectedShape
            if shape:
                self.shapesToItems[shape].setSelected(True)
            else:
                self.labelList.clearSelection()
        # self.actions.delete.setEnabled(selected)
        # self.actions.copy.setEnabled(selected)
        # self.actions.edit.setEnabled(selected)
        # self.actions.shapeLineColor.setEnabled(selected)
        # self.actions.shapeFillColor.setEnabled(selected)

    ###########################################################################
    #                     L A B E L L I S T M E T H O D S                     #
    ###########################################################################

    def labelSelectionChanged(self):
        item = self.currentItem()
        if item:  # and self.canvas.editing():
            self.noSelectionSlot = True
            self.canvas.selectShape(self.itemsToShapes[item])
            shape = self.itemsToShapes[item]
            # Add Chris
            # self.diffcButton.setChecked(shape.difficult)

    def labelItemChanged(self, item):
        shape = self.itemsToShapes[item]
        label = item.text()
        if label != shape.label:
            shape.label = item.text()
            shape.line_color = generateColorByText(shape.label)
            self.setDirty()
        else:  # User probably changed item visibility
            self.canvas.setShapeVisible(shape, item.checkState() == Qt.Checked)

    def currentItem(self):
        items = self.labelList.selectedItems()
        if items:
            return items[0]
        return None

    ###########################################################################
    #                               E V E N T S                               #
    ###########################################################################

    def closeEvent(self, event):
        if not self.mayContinue():
            event.ignore()
        settings = self.settings
        # If it loads images from dir, don't load it at the begining
        if self.foldername is nonePath:
            settings[SETTING_FILENAME] = self.filePath if self.filePath else ''
        else:
            settings[SETTING_FILENAME] = nonePath

        settings[SETTING_WIN_SIZE] = self.size()
        settings[SETTING_WIN_POSE] = self.pos()
        settings[SETTING_WIN_STATE] = self.saveState()
        settings[SETTING_LINE_COLOR] = self.lineColor
        settings[SETTING_FILL_COLOR] = self.fillColor
        settings[SETTING_RECENT_FILES] = self.recentFiles
        if self.labelFolder and self.labelFolder.exists():
            settings[SETTING_LABEL_DIR] = self.labelFolder
        else:
            settings[SETTING_LABEL_DIR] = None

        if self.lastOpenFolder and self.lastOpenFolder.exists():
            settings[SETTING_LAST_OPEN_FOLDER] = self.lastOpenFolder
        else:
            settings[SETTING_LAST_OPEN_FOLDER] = None

        settings[SETTING_AUTO_SAVE] = self.actions.autosaving.isChecked()
        # settings[SETTING_SINGLE_CLASS] = self.singleClassMode.isChecked()
        # settings[SETTING_PAINT_LABEL] = self.displayLabelOption.isChecked()
        # settings[SETTING_DRAW_SQUARE] = self.drawSquaresOption.isChecked()
        settings.save()

    ###########################################################################
    #                              M E T H O D S                              #
    ###########################################################################

    def resetState(self):
        self.itemsToShapes.clear()
        self.shapesToItems.clear()
        self.labelList.clear()
        self.filePath = nonePath
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

    def loadLabels(self, shapes):
        s = []
        for label, points, line_color, fill_color, difficult in shapes:
            shape = Shape(label=label)
            for x, y in points:

                # Ensure the labels are within the bounds of the image.
                # If not, fix them.
                x, y, snapped = self.canvas.snapPointToCanvas(x, y)
                if snapped:
                    self.setDirty()

                shape.addPoint(QPointF(x, y))
            shape.difficult = difficult
            shape.close()
            s.append(shape)

            if line_color:
                shape.line_color = QColor(*line_color)
            else:
                shape.line_color = generateColorByText(label)

            if fill_color:
                shape.fill_color = QColor(*fill_color)
            else:
                shape.fill_color = generateColorByText(label)

            self.addLabel(shape)
        # self.updateComboBox()
        self.canvas.loadShapes(s)

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
        for action in self.actions.onLoadActive:
            action.setEnabled(value)

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

    def __getImageFolder(self):
        return self.__imageFolder

    def __getLabelFolder(self):
        return self.__labelFolder

    def __getFoldername(self):
        return self.__foldername

    def __getLastOpenFolder(self):
        return self.__lastOpenFolder

    def __getAppname(self):
        return self.__appname

    def __getCanvas(self):
        return self.__canvas

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

    def __getMImgList(self):
        return self.__mImgList

    def __getLabelHist(self):
        return self.__labelHist

    def __getFileListWidget(self):
        return self.__fileListWidget

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

    def __getNoSelectionSlot(self):
        return self.__noSelectionSlot

    def __getRecentFiles(self):
        return self.__recentFiles

    def __getMaxRecent(self):
        return self.__maxRecent

    ###########################################################################
    #                               S E T T E R                               #
    ###########################################################################
    def __setActions(self, x):
        if isinstance(x, struct):
            self.__actions = x
        else:
            raise ValueError(x, self.__getStr('structE'))

    def __setFilePath(self, x):
        if isinstance(x, Path) or x is nonePath:
            self.__filePath = x
        else:
            raise ValueError(x, self.__getStr('pathE'))

    def __setImageFolder(self, x):
        if isinstance(x, Path) or x is nonePath:
            self.__imageFolder = x
        else:
            raise ValueError(x, self.__getStr('pathE'))

    def __setLabelFolder(self, x):
        if isinstance(x, Path) or x is nonePath:
            self.__labelFolder = x
        else:
            raise ValueError(x, self.__getStr('pathE'))

    def __setFoldername(self, x):
        if isinstance(x, Path) or x is nonePath:
            self.__foldername = x
        else:
            raise ValueError(x, self.__getStr('pathE'))

    def __setLastOpenFolder(self, x):
        if isinstance(x, Path) or x is nonePath:
            self.__lastOpenFolder = x
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

    def __setMImgList(self, x):
        if isinstance(x, list):
            self.__mImgList = x
        else:
            raise ValueError(x, self.__getStr('listE'))

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

    def __setNoSelectionSlot(self, x):
        if isinstance(x, bool):
            self.__noSelectionSlot = x
        else:
            raise ValueError(x, self.__getStr('boolE'))

    def __setRecentFiles(self, x):
        if isinstance(x, list):
            self.__recentFiles = x
        else:
            raise ValueError(x, self.__getStr('listE'))

    def __setMaxRecent(self, x):
        if isinstance(x, int):
            self.__maxRecent = x
        else:
            raise ValueError(x, self.__getStr('intE'))

    ###########################################################################
    #                           P R O P E R T I E S                           #
    ###########################################################################

    actions = property(__getActions, __setActions)
    filePath = property(__getFilePath, __setFilePath)
    imageFolder = property(__getImageFolder, __setImageFolder)
    labelFolder = property(__getLabelFolder, __setLabelFolder)
    foldername = property(__getFoldername, __setFoldername)
    lastOpenFolder = property(__getLastOpenFolder, __setLastOpenFolder)

    appname = property(__getAppname)
    canvas = property(__getCanvas)
    image = property(__getImage, __setImage)

    selectedClass = property(__getSelectedClass, __setSelectedClass)
    itemsToShapes = property(__getItemsToShapes, __setItemsToShapes)
    shapesToItems = property(__getShapesToItems, __setShapesToItems)
    prevLabelText = property(__getPrevLabelText, __setPrevLabelText)
    dirty = property(__getDirty, __setDirty)

    mImgList = property(__getMImgList, __setMImgList)
    labelHist = property(__getLabelHist, __setLabelHist)
    fileListWidget = property(__getFileListWidget, __setFileListWidget)

    usePascalVocFormat = property(__getUPascalVocFormat, __setUPascalVocFormat)
    useYoloFormat = property(__getUYoloFormat, __setUYoloFormat)
    useBoxSupFormat = property(__getUBoxSupFormat, __setUBoxSupFormat)
    lineColor = property(__getLineColor, __setLineColor)
    fillColor = property(__getFillColor, __setFillColor)
    noSelectionSlot = property(__getNoSelectionSlot, __setNoSelectionSlot)
    recentFiles = property(__getRecentFiles, __setRecentFiles)
    maxRecent = property(__getMaxRecent, __setMaxRecent)
