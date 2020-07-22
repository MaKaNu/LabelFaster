from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from libs.labelFile import LabelFile
from libs.pascal_io import PascalVocReader
from libs.pascal_io import XML_EXT
from libs.yolo_io import YoloReader
from libs.yolo_io import TXT_EXT

import os
import codecs


def openFile(self):
    path = os.path.dirname(self.path) if self.path else '.'
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


def loadFile(self, filePath=None):
    """Load the specified file, or the last opened file if None."""
    # self.resetState()
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
        self.setClean()
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


def loadPredefinedClasses(self, predefClassesFile):
    if predefClassesFile.exists():
        with codecs.open(predefClassesFile, 'r', 'utf8') as f:
            for line in f:
                line = line.strip()
                if self.labelHist is None:
                    self.labelHist = [line]
                else:
                    self.labelHist.append(line)


def read(filename, default=None):
    try:
        with open(filename, 'rb') as f:
            return f.read()
    except FileNotFoundError:
        return default
