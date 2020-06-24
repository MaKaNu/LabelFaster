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

    @staticmethod
    def isLabelFile(filename):
        fileSuffix = os.path.splitext(filename)[1].lower()
        return fileSuffix == LabelFile.suffix
