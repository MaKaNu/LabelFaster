import os

from PyQt5.QtGui import QImage

from libs.pascal_io import PascalVocWriter, XML_EXT
from libs.yolo_io import YOLOWriter, TXT_EXT
from libs.boxsup_io import BOXSUPWriter, PNG_EXT
from libs.utils import nonePath
import os.path


class LabelFileError(Exception):
    pass


class LabelFile(object):
    suffix = XML_EXT
    labelPath = nonePath

    def __init__(self, filename=None):
        self.shape = ()
        self.imagePath = None
        self.imageData = None
        self.verified = False

    def savePascalVocFormat(self, filename, shapes, imagePath, imageData,
                            lineColor=None, fillColor=None, databaseSrc=None):
        self.labelPath = filename
        imgFolderPath = os.path.dirname(imagePath)
        imgFolderName = os.path.split(imgFolderPath)[-1]
        imgFileName = os.path.basename(imagePath)
        # Read from file path because self.imageData might be empty if saving
        # to Pascal format
        image = QImage()
        image.load(str(imagePath))
        imageShape = [image.height(), image.width(),
                      1 if image.isGrayscale() else 3]
        writer = PascalVocWriter(imgFolderName, imgFileName,
                                 imageShape, localImgPath=imagePath)
        writer.verified = self.verified

        for shape in shapes:
            points = shape['points']
            label = shape['label']
            bndbox = LabelFile.convertPoints2BndBox(points)
            writer.addBndBox(bndbox[0], bndbox[1], bndbox[2], bndbox[3], label)

        writer.save(targetFile=filename)
        return

    def saveYoloFormat(
            self, filename, shapes, imagePath, imageData, classList,
            lineColor=None, fillColor=None, databaseSrc=None):
        self.labelPath = filename
        imgFolderPath = os.path.dirname(imagePath)
        imgFolderName = os.path.split(imgFolderPath)[-1]
        imgFileName = os.path.basename(imagePath)
        # Read from file path because self.imageData might be empty if saving
        # to Pascal format
        image = QImage()
        image.load(str(imagePath))
        imageShape = [image.height(), image.width(),
                      1 if image.isGrayscale() else 3]
        writer = YOLOWriter(
            imgFolderName, imgFileName,
            imageShape, localImgPath=imagePath)
        writer.verified = self.verified

        for shape in shapes:
            points = shape['points']
            label = shape['label']
            bndbox = LabelFile.convertPoints2BndBox(points)
            writer.addBndBox(bndbox[0], bndbox[1], bndbox[2], bndbox[3], label)

        writer.save(targetFile=filename, classList=classList)
        return

    def saveBoxSupFormat(
            self, filename, shapes, imagePath, imageData, classList,
            lineColor=None, fillColor=None, databaseSrc=None):
        self.labelPath = filename
        imgFolderPath = os.path.dirname(imagePath)
        imgFolderName = os.path.split(imgFolderPath)[-1]
        imgFileName = os.path.basename(imagePath)
        image = QImage()
        image.load(str(imagePath))
        imageShape = [image.height(), image.width(),
                      1 if image.isGrayscale() else 3]
        writer = BOXSUPWriter(
            imgFolderName, imgFileName,
            imageShape, localImgPath=imagePath)
        # writer.verified = self.verified

        for shape in shapes:
            points = shape['points']
            label = shape['label']
            color = shape['fill_color']
            bndbox = LabelFile.convertPoints2BndBox(points)
            writer.addBndBox(
                bndbox[0], bndbox[1], bndbox[2], bndbox[3],
                label, color)

        writer.save(targetFile=filename, classList=classList)
        return

    def toggleVerify(self):
        self.verified = not self.verified

    def changePath(self, path):
        self.labelPath = path

    @staticmethod
    def isLabelFile(filename):
        suffix = filename.suffix.lower()
        return suffix == LabelFile.suffix and suffix != '.png'

    @staticmethod
    def convertPoints2BndBox(points):
        xmin = float('inf')
        ymin = float('inf')
        xmax = float('-inf')
        ymax = float('-inf')
        for p in points:
            x = p[0]
            y = p[1]
            xmin = min(x, xmin)
            ymin = min(y, ymin)
            xmax = max(x, xmax)
            ymax = max(y, ymax)

        # set values below 1 to 1 for faster-rcnn
        if xmin < 1:
            xmin = 1

        if ymin < 1:
            ymin = 1

        return (int(xmin), int(ymin), int(xmax), int(ymax))
