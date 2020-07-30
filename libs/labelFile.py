import os

from PyQt5.QtGui import QImage


XML_EXT = '.xml'


class LabelFile(object):
    suffix = XML_EXT

    def __init__(self, filename=None):
        self.shape = ()
        self.imagePath = None
        self.imageData = None
        self.verified = False


    def saveBoxSupFormat(
            self, filename, shapes, imagePath, imageData, classList,
            lineColor=None, fillColor=None, databaseSrc=None):
        imgFolderPath = os.path.dirname(imagePath)
        imgFolderName = os.path.split(imgFolderPath)[-1]
        imgFileName = os.path.basename(imagePath)
        image = QImage()
        image.load(imagePath)
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

    def changeExt(self, ext):
        self.suffix = ext

    @staticmethod
    def isLabelFile(filename):
        fileSuffix = os.path.splitext(filename)[1].lower()
        return fileSuffix == LabelFile.suffix

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
