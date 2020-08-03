from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from pathlib import Path

from libs.labelFile import LabelFile, LabelFileError
from libs.utils import natural_sort, nonePath
from libs.pascal_io import PascalVocReader, XML_EXT
from libs.yolo_io import YoloReader, TXT_EXT
from libs.boxsup_io import BOXSUPReader, PNG_EXT

from libs.messages import discardChangesDialog
from libs.constants import *

import os
import codecs


def openFile(self):
    if not self.mayContinue():
        return
    path = self.filePath.parents[0] if self.filePath else Path()
    formats = [
        '*.%s' % fmt.data().decode("ascii").lower()
        for fmt in QImageReader.supportedImageFormats()]
    filters = "Image & Label files (%s)" % ' '.join(
        formats +
        ['*%s' % LabelFile.suffix])
    filename = QFileDialog.getOpenFileName(
        None,
        '%s - Choose Image or Label file' % self.appname,
        str(path.absolute()), filters)
    if all(filename):
        if isinstance(filename, (tuple, list)):
            filename = Path(filename[0])
        self.loadFile(filename)
    else:
        pass
        # TODO errormessage to inform that something went wrong


def openFolder(self, silent=False):
    if not self.mayContinue():
        return

    if self.lastOpenFolder and self.lastOpenFolder.exists():
        defaultOpenDirPath = self.lastOpenDir
    else:
        defaultOpenDirPath = self.filePath.parent \
            if self.filePath.exists() else Path()
    if not silent:
        targetDirPath = QFileDialog.getExistingDirectory(
            self,
            '%s - Open Directory' % self.appname,
            str(defaultOpenDirPath.absolute()),
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
        targetDirPath = Path(targetDirPath)
    else:
        targetDirPath = defaultOpenDirPath

    self.importFolderImgs(targetDirPath)


def importFolderImgs(self, dirpath):
    if not self.mayContinue() or not dirpath:
        return

    self.lastOpenDir = dirpath
    self.dirname = dirpath
    self.filePath = nonePath
    self.fileListWidget.clear()
    self.mImgList = self.scanAllImages(dirpath)
    self.openNextImg()
    for imgPath in self.mImgList:
        item = QListWidgetItem(str(imgPath))
        self.fileListWidget.addItem(item)


def scanAllImages(self, folderPath):
    extensions = [
        '.%s' % fmt.data().decode("ascii").lower()
        for fmt in QImageReader.supportedImageFormats()]
    images = []

    for file in folderPath.glob('*'):
        if file.suffix.lower() in extensions:
            images.append(file.absolute())

    natural_sort(images, key=lambda x: str(x).lower())
    return images


def openPrevImg(self, _value=False):
    # Proceding prev image without dialog if having any label
    if self.autoSaving.isChecked():
        if self.labelFolder is not nonePath:
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
        if self.labelFolder is not nonePath:
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
    if self.filePath is nonePath:
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
    else:
        filePath = Path(filePath)

    # Get absolute Filepath
    absoluteFilePath = filePath.absolute()

    if absoluteFilePath and absoluteFilePath.exists():
        if LabelFile.isLabelFile(absoluteFilePath):
            try:
                self.labelFile = LabelFile(absoluteFilePath)
            except LabelFileError as e:
                self.errorMessage(u'Error opening file', (
                    u"<p><b>%s</b></p>"
                    u"<p>Make sure <i>%s</i> is a valid label file."
                    ) % (e, absoluteFilePath)
                    )
                self.status("Error reading %s" % absoluteFilePath)
                return False
            self.imageData = self.labelFile.imageData
            self.lineColor = QColor(*self.labelFile.lineColor)
            self.fillColor = QColor(*self.labelFile.fillColor)
            self.canvas.verified = self.labelFile.verified
        else:
            # Load image:
            # read data first and store for saving into label file.
            self.imageData = read(absoluteFilePath, None)
            self.labelFile = None
            self.canvas.verified = False
            self.imageFolder = absoluteFilePath.parent

        image = QImage.fromData(self.imageData)
        if image.isNull():
            self.errorMessage(
                u'Error opening file',
                u"<p>Make sure <i>%s</i> is a valid image file."
                % absoluteFilePath
                )
            self.status("Error reading %s" % absoluteFilePath)
            return False
        self.status("Loaded %s" % absoluteFilePath.name)
        self.image = image
        self.filePath = absoluteFilePath
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
        if self.labelFolder is not nonePath:
            basename = self.filePath.stem
            xmlPath = self.labelFolder / Path(basename + XML_EXT)
            txtPath = self.labelFolder / Path(basename + TXT_EXT)

            """Annotation file priority:
            PascalXML > YOLO
            """
            if os.path.isfile(xmlPath):
                self.loadPascalXMLByFilename(xmlPath)
            elif os.path.isfile(txtPath):
                self.loadYOLOTXTByFilename(txtPath)

        self.setWindowTitle(self.appname + ' ' + str(filePath.absolute()))

        # Default : select last item if there is at least one item
        # if self.labelList.count():
        #     self.labelList.setCurrentItem(self.labelList.item(self.labelList.count()-1))
        #     self.labelList.item(self.labelList.count()-1).setSelected(True)

        self.canvas.setFocus(True)
        return True
    return False


def changeSaveFolderDialog(self, _value=False):
    if self.labelFolder is not nonePath:
        path = self.labelFolder
    else:
        path = '.'

    dirpath = QFileDialog.getExistingDirectory(
        self,
        '%s - Save annotations to the directory' % self.appname,
        path,
        QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)

    if dirpath is not nonePath and len(dirpath) > 1:
        self.labelFolder = dirpath

    self.statusBar().showMessage(
        '%s . Annotation will be saved to %s' %
        ('Change saved folder', self.labelFolder))
    self.statusBar().show()


def saveFile(self, _value=False):
    if self.labelFolder is not nonePath:
        if self.filePath:
            imgFileName = self.filePath.stem
            savedPath = self.labelFolder / Path(imgFileName)
            self.initiateSaveProcess(savedPath)
    else:
        self.initiateSaveProcess(
            self.labelFile.labelPath if self.labelFile
            else self.saveFileDialog(removeExt=False))


def saveFileDialog(self, removeExt=True):
    caption = '%s - Choose File' % self.appname
    filters = 'File (*%s)' % LabelFile.suffix
    openDialogPath = self.currentPath()
    dlg = QFileDialog(self, caption, str(openDialogPath), filters)
    dlg.setDefaultSuffix(LabelFile.suffix[1:])
    dlg.setAcceptMode(QFileDialog.AcceptSave)
    filenameWithoutExtension = self.filePath.with_suffix('')
    dlg.selectFile(str(filenameWithoutExtension))
    dlg.setOption(QFileDialog.DontUseNativeDialog, False)
    if dlg.exec_():
        fullFilePath = Path(dlg.selectedFiles()[0])
        if removeExt:
            # Return file path without the extension.
            return fullFilePath.with_suffix('')
        else:
            return fullFilePath
    return ''


def initiateSaveProcess(self, annotationFilePath):
    if annotationFilePath and self.saveLabels(annotationFilePath):
        self.dirty = False
        self.labelFolder = annotationFilePath.parent
        self.statusBar().showMessage('Saved to  %s' % annotationFilePath)
        self.statusBar().show()


def saveLabels(self, annotationFilePath):
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
            if annotationFilePath.suffix.lower() != ".xml":
                annotationFilePath = annotationFilePath.with_suffix(XML_EXT)
            self.labelFile.savePascalVocFormat(
                annotationFilePath,
                shapes,
                self.filePath,
                self.imageData,
                self.lineColor.getRgb(),
                self.fillColor.getRgb())
        elif self.useYoloFormat is True:
            if annotationFilePath.suffix.lower() != ".txt":
                annotationFilePath = annotationFilePath.with_suffix(TXT_EXT)
            self.labelFile.saveYoloFormat(
                annotationFilePath,
                shapes,
                self.filePath,
                self.imageData,
                self.labelHist,
                self.lineColor.getRgb(),
                self.fillColor.getRgb())
        elif self.useBoxSupFormat is True:
            if annotationFilePath.suffix.lower() != ".png":
                annotationFilePath = annotationFilePath.with_suffix(PNG_EXT)
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
    if not self.mayContinue():
        return
    currIndex = self.mImgList.index(Path(item.text()))
    if currIndex < len(self.mImgList):
        filename = self.mImgList[currIndex]
        if filename:
            self.loadFile(filename)


def mayContinue(self):
    return not (self.dirty and not discardChangesDialog(self))


def currentPath(self):
    return self.filePath.parent if self.filePath else '.'


def read(filename, default=None):
    try:
        with open(filename, 'rb') as f:
            return f.read()
    except FileNotFoundError:
        return default
