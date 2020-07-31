from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from libs.labelFile import LabelFile, LabelFileError
from libs.utils import natural_sort
from libs.pascal_io import PascalVocReader, XML_EXT
from libs.yolo_io import YoloReader, TXT_EXT
from libs.boxsup_io import BOXSUPReader, PNG_EXT

from libs.messages import discardChangesDialog
from libs.constants import *

import os
import codecs


def openFile(self):
    path = os.path.dirname(self.filePath) if self.filePath else '.'
    formats = [
        '*.%s' % fmt.data().decode("ascii").lower()
        for fmt in QImageReader.supportedImageFormats()]
    filters = "Image & Label files (%s)" % ' '.join(
        formats +
        ['*%s' % LabelFile.suffix])
    filename = QFileDialog.getOpenFileName(
        None,
        '%s - Choose Image or Label file' % self.appname, path, filters)
    if all(filename):
        if isinstance(filename, (tuple, list)):
            filename = filename[0]
        self.loadFile(filename)
    elif filename[0] == '':
        pass  # Set a variable later to stop throwing the wrong datatype message


def openFolder(self, silent=False):
    if not self.mayContinue():
        return

    if self.lastOpenFolder and os.path.exists(self.lastOpenFolder):
        defaultOpenDirPath = self.lastOpenDir
    else:
        defaultOpenDirPath = os.path.dirname(self.filePath) \
            if self.filePath else '.'
    if not silent:
        targetDirPath = QFileDialog.getExistingDirectory(
            self,
            '%s - Open Directory' % self.appname,
            defaultOpenDirPath,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
    else:
        targetDirPath = defaultOpenDirPath

    self.importFolderImgs(targetDirPath)


def importFolderImgs(self, dirpath):
    if not self.mayContinue() or not dirpath:
        return

    self.lastOpenDir = dirpath
    self.dirname = dirpath
    self.filePath = None
    self.fileListWidget.clear()
    self.mImgList = self.scanAllImages(dirpath)
    self.openNextImg()
    for imgPath in self.mImgList:
        item = QListWidgetItem(imgPath)
        self.fileListWidget.addItem(item)


def scanAllImages(self, folderPath):
    extensions = [
        '.%s' % fmt.data().decode("ascii").lower()
        for fmt in QImageReader.supportedImageFormats()]
    images = []

    for root, _, files in os.walk(folderPath):
        for file in files:
            if file.lower().endswith(tuple(extensions)):
                relativePath = os.path.join(root, file)
                path = os.path.abspath(relativePath)
                images.append(path)
    natural_sort(images, key=lambda x: x.lower())
    return images


def openPrevImg(self, _value=False):
    # Proceding prev image without dialog if having any label
    if self.autoSaving.isChecked():
        if self.defaultSaveDir is not None:
            if self.dirty is True:
                self.saveFile()
        else:
            self.changeSavedirDialog()
            return

    if not self.mayContinue():
        return

    if len(self.mImgList) <= 0:
        return

    if self.filePath is None:
        return

    currIndex = self.mImgList.index(self.filePath)
    if currIndex - 1 >= 0:
        filename = self.mImgList[currIndex - 1]
        if filename:
            self.loadFile(filename)


def openNextImg(self, _value=False):
    # Proceding prev image without dialog if having any label
    if self.actions.autosaving.isChecked():
        if self.defaultSaveDir is not None:
            if self.dirty is True:
                self.saveFile()
        else:
            self.changeSavedirDialog()
            return

    if not self.mayContinue():
        return

    if len(self.mImgList) <= 0:
        return

    filename = None
    if self.filePath is None:
        filename = self.mImgList[0]
    else:
        currIndex = self.mImgList.index(self.filePath)
        if currIndex + 1 < len(self.mImgList):
            filename = self.mImgList[currIndex + 1]

    if filename:
        self.loadFile(filename)


def loadFile(self, filePath=None):
    """Load the specified file, or the last opened file if None."""
    self.resetState()
    # self.canvas.setEnabled(False)
    if filePath is None:
        filePath = self.settings.get(SETTING_FILENAME)

    # Fix bug: An  index error after select a directory when open a new file.
    unicodeFilePath = os.path.abspath(filePath)

    if unicodeFilePath and os.path.exists(unicodeFilePath):
        if LabelFile.isLabelFile(unicodeFilePath):
            try:
                self.labelFile = LabelFile(unicodeFilePath)
            except LabelFileError as e:
                self.errorMessage(u'Error opening file', (
                    u"<p><b>%s</b></p>"
                    u"<p>Make sure <i>%s</i> is a valid label file."
                    ) % (e, unicodeFilePath)
                    )
                self.status("Error reading %s" % unicodeFilePath)
                return False
            self.imageData = self.labelFile.imageData
            self.lineColor = QColor(*self.labelFile.lineColor)
            self.fillColor = QColor(*self.labelFile.fillColor)
            self.canvas.verified = self.labelFile.verified
        else:
            # Load image:
            # read data first and store for saving into label file.
            self.imageData = read(unicodeFilePath, None)
            self.labelFile = None
            self.canvas.verified = False

        image = QImage.fromData(self.imageData)
        if image.isNull():
            self.errorMessage(
                u'Error opening file',
                u"<p>Make sure <i>%s</i> is a valid image file."
                % unicodeFilePath
                )
            self.status("Error reading %s" % unicodeFilePath)
            return False
        self.status("Loaded %s" % os.path.basename(unicodeFilePath))
        self.image = image
        self.filePath = unicodeFilePath
        self.canvas.loadPixmap(QPixmap.fromImage(image))
        if self.labelFile:
            self.loadLabels(self.labelFile.shapes)
        self.dirty = False
        self.canvas.setEnabled(True)
        self.adjustScale(initial=True)
        self.paintCanvas()
        # self.addRecentFile(self.filePath)
        self.toggleActions(True)

        # Label xml file and show bound box according to its filename
        # if self.usingPascalVocFormat is True:
        if self.defaultSaveDir is not None:
            basename = os.path.basename(
                os.path.splitext(self.filePath)[0])
            xmlPath = os.path.join(self.defaultSaveDir, basename + XML_EXT)
            txtPath = os.path.join(self.defaultSaveDir, basename + TXT_EXT)

            """Annotation file priority:
            PascalXML > YOLO
            """
            if os.path.isfile(xmlPath):
                self.loadPascalXMLByFilename(xmlPath)
            elif os.path.isfile(txtPath):
                self.loadYOLOTXTByFilename(txtPath)
        else:
            xmlPath = os.path.splitext(filePath)[0] + XML_EXT
            txtPath = os.path.splitext(filePath)[0] + TXT_EXT
            if os.path.isfile(xmlPath):
                self.loadPascalXMLByFilename(xmlPath)
            elif os.path.isfile(txtPath):
                self.loadYOLOTXTByFilename(txtPath)

        self.setWindowTitle(self.appname + ' ' + filePath)

        # Default : select last item if there is at least one item
        # if self.labelList.count():
        #     self.labelList.setCurrentItem(self.labelList.item(self.labelList.count()-1))
        #     self.labelList.item(self.labelList.count()-1).setSelected(True)

        self.canvas.setFocus(True)
        return True
    return False


def changeSaveFolderDialog(self, _value=False):
    if self.defaultSaveDir is not None:
        path = self.defaultSaveDir
    else:
        path = '.'

    dirpath = QFileDialog.getExistingDirectory(
        self,
        '%s - Save annotations to the directory' % self.appname,
        path,
        QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)

    if dirpath is not None and len(dirpath) > 1:
        self.defaultSaveDir = dirpath

    self.statusBar().showMessage(
        '%s . Annotation will be saved to %s' %
        ('Change saved folder', self.defaultSaveDir))
    self.statusBar().show()


def saveFile(self, _value=False):
    if self.defaultSaveDir is not None and len(self.defaultSaveDir):
        if self.filePath:
            imgFileName = os.path.basename(self.filePath)
            savedFileName = os.path.splitext(imgFileName)[0]
            savedPath = os.path.join(self.defaultSaveDir, savedFileName)
            self.selectSaveFile(savedPath)
    else:
        self.selectSaveFile(
            self.labelFile.labelPath if self.labelFile
            else self.saveFileDialog(removeExt=False))


def saveFileDialog(self, removeExt=True):
    caption = '%s - Choose File' % self.appname
    filters = 'File (*%s)' % LabelFile.suffix
    openDialogPath = self.currentPath()
    dlg = QFileDialog(self, caption, openDialogPath, filters)
    dlg.setDefaultSuffix(LabelFile.suffix[1:])
    dlg.setAcceptMode(QFileDialog.AcceptSave)
    filenameWithoutExtension = os.path.splitext(self.filePath)[0]
    dlg.selectFile(filenameWithoutExtension)
    dlg.setOption(QFileDialog.DontUseNativeDialog, False)
    if dlg.exec_():
        fullFilePath = dlg.selectedFiles()[0]
        if removeExt:
            # Return file path without the extension.
            return os.path.splitext(fullFilePath)[0]
        else:
            return fullFilePath
    return ''


def selectSaveFile(self, annotationFilePath):
    if annotationFilePath and self.saveLabels(annotationFilePath):
        self.dirty = False
        self.statusBar().showMessage('Saved to  %s' % annotationFilePath)
        self.statusBar().show()


def saveLabels(self, annotationFilePath):
    annotationFilePath = annotationFilePath
    if self.labelFile is None:
        self.labelFile = LabelFile()
        self.labelFile.verified = self.canvas.verified

    def format_shape(s):
        return dict(
            label=s.label,
            line_color=s.line_color.getRgb(),
            fill_color=s.fill_color.getRgb(),
            points=[(p.x(), p.y()) for p in s.points]
            )

    shapes = [format_shape(shape) for shape in self.canvas.shapes]
    # Can add differrent annotation formats here
    try:
        if self.usePascalVocFormat is True:
            if annotationFilePath[-4:].lower() != ".xml":
                annotationFilePath += XML_EXT
            self.labelFile.savePascalVocFormat(
                annotationFilePath,
                shapes,
                self.filePath,
                self.imageData,
                self.lineColor.getRgb(),
                self.fillColor.getRgb())
        elif self.useYoloFormat is True:
            if annotationFilePath[-4:].lower() != ".txt":
                annotationFilePath += TXT_EXT
            self.labelFile.saveYoloFormat(
                annotationFilePath,
                shapes,
                self.filePath,
                self.imageData,
                self.labelHist,
                self.lineColor.getRgb(),
                self.fillColor.getRgb())
        elif self.useBoxSupFormat is True:
            if annotationFilePath[-4:].lower() != ".png":
                annotationFilePath += PNG_EXT
            self.labelFile.saveBoxSupFormat(
                annotationFilePath,
                shapes,
                self.filePath,
                self.imageData,
                self.labelHist,
                self.lineColor.getRgb(),
                self.fillColor.getRgb())
        else:
            self.labelFile.save(
                annotationFilePath, shapes, self.filePath, self.imageData,
                self.lineColor.getRgb(), self.fillColor.getRgb())
        print('Image:{0} -> Annotation:{1}'.format(
            self.filePath, annotationFilePath))
        return True
    except LabelFileError as e:
        self.errorMessage(u'Error saving label data', u'<b>%s</b>' % e)
        return False


def loadPredefinedClasses(self, predefClassesFile):
    if predefClassesFile.exists():
        with codecs.open(predefClassesFile, 'r', 'utf8') as f:
            for line in f:
                line = line.strip()
                if self.labelHist is None:
                    self.labelHist = [line]
                else:
                    self.labelHist.append(line)


def fileitemDoubleClicked(self, item=None):
    currIndex = self.mImgList.index(item.text())
    if currIndex < len(self.mImgList):
        filename = self.mImgList[currIndex]
        if filename:
            self.loadFile(filename)


def mayContinue(self):
    return not (self.dirty and not discardChangesDialog(self))


def currentPath(self):
    return os.path.dirname(self.filePath) if self.filePath else '.'


def read(filename, default=None):
    try:
        with open(filename, 'rb') as f:
            return f.read()
    except FileNotFoundError:
        return default
