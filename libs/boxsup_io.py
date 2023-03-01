import os
from os import path

from PyQt5.QtCore import Qt, QRect
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QImage, QPainter, QColor

from libs.utils import nonePath, generateColorByText
from pathlib import Path
import numpy as np
import scipy.io

PNG_EXT = '.png'
MAT_EXT = '.mat'


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

    def BndBox2BoxSupImg(self, classList=[]):

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
            painter.fillRect(QRect(int(x), int(y), int(w), int(h)), QColor(*color))

            boxName = box['name']
            if boxName not in classList:
                classList.append(boxName)

        painter.end()
        return image, classList

    def BndBox2BoxSupMask(self, classList=[]):
        mask = np.zeros((self.imgSize[1], self.imgSize[0]), dtype=int)

        for box in self.boxlist:

            boxName = box['name']
            if boxName not in classList:
                classList.append(boxName)

            x_min = box['xmin']
            y_min = box['ymin']
            x_max = x_min + int(box['w'])
            y_max = y_min + int(box['h'])

            temp_mask = np.ones((x_max-x_min, y_max-y_min)) * \
                (classList.index(boxName) + 1)

            mask[x_min:x_max, y_min:y_max] = temp_mask

        return np.transpose(mask), classList

    def save(self, use_mask, classList=[], targetFile=nonePath):
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

        if use_mask:
            mask, classList = self.BndBox2BoxSupMask(classList)
            scipy.io.savemat(str(out_file), {'mask_data': mask})
        else:
            image, classList = self.BndBox2BoxSupImg(classList)
            image.save(str(out_file))

        out_class_file.write('Class,R,G,B\n')
        for c in classList:
            color = generateColorByText(c).getRgb()[:-1]
            out_class_file.write(c + ', ' + str(color)[1:-1] + '\n')

        out_class_file.close()


class BOXSUPReader:
    pass
