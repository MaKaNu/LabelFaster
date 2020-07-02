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
