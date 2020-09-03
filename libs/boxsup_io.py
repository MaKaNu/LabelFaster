import os
from os import path

from PyQt5.QtCore import Qt, QRect
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QImage, QPainter, QColor

from libs.utils import nonePath, generateColorByText
from pathlib import Path

PNG_EXT = '.png'


class BOXSUPWriter(QWidget):
    def __init__(
            self, foldername, filename, imgSize, databaseSrc='Unknown',
            localImgPath=None):
        super().__init__()
        self.foldername = foldername
        self.filename = filename
        self.databaseSrc = databaseSrc
        self.imgSize = imgSize
        self.image = QImage(imgSize[1], imgSize[0], QImage.Format_RGB32)
        self.boxlist = []
        self.localImgPath = localImgPath
        self.verified = False

    def addBndBox(self, xmin, ymin, xmax, ymax, name, color, difficult=False):
        bndbox = {
            'xmin': xmin, 'ymin': ymin,
            'w': float(xmax - xmin), 'h': float(ymax - ymin)}
        bndbox['name'] = name
        bndbox['color'] = color
        bndbox['difficult'] = difficult
        self.boxlist.append(bndbox)

    def BndBox2BoxSupImg(self, box, classList=[]):

        image = QImage(self.imgSize[1], self.imgSize[0], QImage.Format_RGB32)
        image.fill(Qt.black)

        painter = QPainter(image)
        for box in self.boxlist:
            x = box['xmin']
            y = box['ymin']
            w = box['w']
            h = box['h']
            color_ = box['color']
            color = color_[0:3] + (255,)
            painter.fillRect(QRect(x, y, w, h), QColor(*color))

            boxName = box['name']
            if boxName not in classList:
                classList.append(boxName)

        painter.end()
        return image

    def save(self, classList=[], targetFile=nonePath):

        out_file = None  # Update yolo .txt
        out_class_file = None   # Update class list .txt

        if targetFile is nonePath:
            out_file = self.filename
        else:
            out_file = targetFile
        out_file = out_file.parent / \
            (out_file.stem + '_label' + out_file.suffix)

        classesFile = targetFile.parent / Path('classes_bxsp.txt')
        out_class_file = open(classesFile, 'w')

        image = self.BndBox2BoxSupImg(self.boxlist, classList)

        image.save(str(out_file))

        out_class_file.write('Class,R,G,B\n')
        for c in classList:
            color = generateColorByText(c).getRgb()[:-1]
            out_class_file.write(c + ', ' + str(color)[1:-1] + '\n')

        out_class_file.close()


class BOXSUPReader:
    pass
