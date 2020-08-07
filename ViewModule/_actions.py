import re
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from functools import partial
from collections import Counter
from functools import partial

from libs.utils import newAction, fmtShortcut
from libs.stringBundle import StringBundle
from libs.errors import ClassesError
from libs.settings import Settings
from libs.constants import *

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


def get_openfolder(self):
    openfolder = newAction(
        self,
        getStr('folder'),
        self.openFolder,
        'Ctrl+Shift+O',
        'folder',
        getStr('folderFull'))
    return openfolder


def get_startlabel(self):
    startlabel = newAction(
        self,
        getStr('start'),
        self.setCreateMode,
        'G',
        'start',
        getStr('startFull'),
        enabled=False)
    return startlabel


def get_delete(self):
    delete = newAction(
        self,
        getStr('delBox'),
        self.deleteSelectedShape,
        'Delete',
        'delete',
        getStr('delBoxFull'),
        enabled=False)
    return delete


def get_save(self):
    save = newAction(
        self,
        getStr('save'),
        self.saveFile,
        'Ctrl+s',
        'save',
        getStr('saveFull'),
        enabled=False)
    return save


def get_changesavefolder(self):
    changesavefolder = newAction(
        self,
        getStr('changeSaveFolder'),
        self.changeSaveFolderDialog,
        'Ctrl+Alt+s',
        'folder')
    return changesavefolder


def get_saveformat(self):
    saveformat = newAction(
        self,
        getStr('PascalVOC'),
        self.changeFormat,
        'Ctrl+',
        'format_voc',
        getStr('saveformatFull'),
        enabled=True)
    return saveformat


def get_autosaving(self):
    autosaving = newAction(
        self,
        getStr('autoSave'),
        icon='savemode')
    autosaving.setCheckable(True)
    autosaving.setChecked(self.settings.get(SETTING_AUTO_SAVE, False))
    return autosaving


def get_openNextImg(self):
    openNextImg = newAction(
        self,
        getStr('nextImg'),
        self.openNextImg,
        'd',
        'next',
        getStr('nextImgFull'))
    return openNextImg


def get_openPrevImg(self):
    openPrevImg = newAction(
        self,
        getStr('prevImg'),
        self.openPrevImg,
        'a',
        'prev',
        getStr('prevImgFull'))
    return openPrevImg



def get_zoom(self):
    zoom = QWidgetAction(self)
    zoom.setDefaultWidget(self.zoomWidget)
    self.zoomWidget.setWhatsThis(
        u"Zoom in or out of the image. Also accessible with"
        " %s and %s from the canvas." % (fmtShortcut("Ctrl+[-+]"),
                                         fmtShortcut("Ctrl+Wheel")))
    self.zoomWidget.setEnabled(False)
    return zoom


def get_zoomin(self):
    zoomIn = newAction(
        self,
        getStr('zoomIn'),
        partial(self.addZoom, 10),
        'Ctrl++',
        'zoom-in',
        getStr('zoomInFull'),
        enabled=False
    )
    return zoomIn


def get_zoomout(self):
    zoomOut = newAction(
        self,
        getStr('zoomOut'),
        partial(self.addZoom, -10),
        'Ctrl+-',
        'zoom-out',
        getStr('zoomOutFull'),
        enabled=False
    )
    return zoomOut


def get_zoomorg(self):
    zoomOrg = newAction(
        self,
        getStr('zoomOrg'),
        partial(self.setZoom, 100),
        'Ctrl+=',
        'zoom-org',
        getStr('zoomOrgFull'),
        enabled=False
    )
    return zoomOrg


def get_fitwindow(self):
    fitWindow = newAction(
        self,
        getStr('fitWin'),
        self.setFitWindow,
        'Ctrl+F',
        'fit-window',
        getStr('fitWinFull'),
        checkable=True,
        enabled=False
    )
    return fitWindow


def get_fitwidth(self):
    fitWindow = newAction(
        self,
        getStr('fitWidth'),
        self.setFitWidth,
        'Ctrl+Shift+F',
        'fit-width',
        getStr('fitWidthFull'),
        checkable=True,
        enabled=False
    )
    return fitWindow


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
