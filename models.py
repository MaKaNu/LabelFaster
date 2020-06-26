import cv2
import os
from pathlib import Path
import hashlib
import re

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from libs.labelFile import LabelFile

from pynput.keyboard import Key, Listener, KeyCode


class FileWrapper(QObject):
    __appname__ = 'ROISA - Region of Interest Selector Automat'

    def __init__(self, Widget, filepath='.'):
        super().__init__()
        self.__widget = Widget
        self.__path = filepath
        self.appname = 'ROISA - Region of Interest Selector Automat'

    def openFile(self):
        path = os.path.dirname(self.__path) if self.__path else '.'
        formats = [
            '*.%s' % fmt.data().decode("ascii").lower()
            for fmt in QImageReader.supportedImageFormats()]
        filters = "Image & Label files (%s)" % ' '.join(
            formats +
            ['*%s' % LabelFile.suffix])
        filename = QFileDialog.getOpenFileName(
            None,
            '%s - Choose Image or Label file' % self.appname, path, filters)
        if filename:
            if isinstance(filename, (tuple, list)):
                filename = filename[0]
            self.loadFile(filename)

    def loadFile(self, filePath=None):
        """Load the specified file, or the last opened file if None."""
        # self.resetState()
        # self.canvas.setEnabled(False)
        if filePath is None:
            filePath = self.parent.settings.get(SETTING_FILENAME)

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
                self.__widget.canvas.verified = False

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
            self.addRecentFile(self.filePath)
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

            self.setWindowTitle(__appname__ + ' ' + filePath)

            # Default : select last item if there is at least one item
            if self.labelList.count():
                self.labelList.setCurrentItem(self.labelList.item(self.labelList.count()-1))
                self.labelList.item(self.labelList.count()-1).setSelected(True)

            self.canvas.setFocus(True)
            return True
        return False


class KeyMonitor(QObject):
    keyPressed = pyqtSignal(KeyCode)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.listener = Listener(on_release=self.on_release)

    def on_release(self, key):
        # self.keyPressed.emit(key)
        if not(hasattr(key, 'char')):
            return
        if key.char == 'm':
            if self.parent().chb_multi.isChecked():
                self.parent().chb_multi.setChecked(False)
            else:
                self.parent().chb_multi.setChecked(True)

    def stop_monitoring(self):
        self.listener.stop()

    def start_monitoring(self):
        self.listener.start()


class ROI_controller(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.r = None

    def create_selector(self, im):
        showCrosshair = True
        fromCenter = False
        cv2.namedWindow("Image")
        cv2.moveWindow("Image", int(1920/2), 100)
        self.r = cv2.selectROI("Image", im)

    def crop_image(self, im):
        string = self.parent().selectedImSize
        m = re.findall(r'(?<=x)(\d*)|(\d*)(?=x)', string)
        r = list(self.r)
        if not(self.parent().chb_strech.isChecked()):
            x = abs(r[1] - r[3])
            y = abs(r[0] - r[2])
            if r[3] > r[2]:
                r[0] = r[0] - abs(r[3]-r[2])/2
                r[2] = r[3]
            elif r[3] < r[2]:
                r[1] = r[1] - abs(r[3]-r[2])/2
                r[3] = r[2]

        imCrop = im[int(r[1]):int(r[1]+r[3]), int(r[0]):int(r[0]+r[2])]
        w = int(m[0][1])
        h = int(m[2][0])
        newsize = (h, w)
        if sum(r) != 0:
            imCrop = cv2.resize(imCrop, newsize)
        return imCrop

    def close_selector(self):
        # cv2.waitKey(0)
        cv2.destroyWindow("Image")


# class image_loader(QObject):
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.im_filenames = []
#         self.im_names = []
#         self.im = None
#         self.imcrop = None
#         self.path = None

#     def load_image(self, path):
#         self.im = cv2.imread(str(path))

#     def save_image(self, path, im):
#         im_hash = hashlib.md5(im.copy(order='C')).hexdigest()
#         im_hash = im_hash[0:10] + '.png'
#         self.path = path / Path(im_hash)
#         cv2.imwrite(str(self.path), im)

#     def search_images(self, path):
#         ext = ['.png', '.jpg']
#         for file in os.listdir(path):
#             if file.endswith(tuple(ext)):
#                 self.im_filenames.append(path / Path(file))
#                 self.im_names.append(file)

#     def __str__(self):
#         return 'Image_loader for folder "{}"'.format(self.foldername)


def read(filename, default=None):
    try:
        with open(filename, 'rb') as f:
            return f.read()
    except FileNotFoundError:
        return default


# For TESTING
if __name__ == '__main__':
    im = image_loader('Steine')
    print(im)
    im.search_folder()
    print(im.im_folder)
