from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from libs.stringBundle import StringBundle
from libs.errors import *

class Canvas(QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__pixmap = QPixmap()
        self.__shapes = []
        self.__verified = False

        # Load string bundle for i18n
        self.__stringBundle = StringBundle.getBundle()

    def loadPixmap(self, pixmap):
        self.pixmap = pixmap
        self.shapes = []
        self.repaint()

    ###########################################################################
    #                               G E T T E R                               #
    ###########################################################################

    def __getStr(self, strId):
        return self.__stringBundle.getString(strId)

    def __getVerified(self):
        return self.__verified

    def __getPixmap(self):
        return self.__pixmap

    def __getShapes(self):
        return self.__shapes

    ###########################################################################
    #                               S E T T E R                               #
    ###########################################################################

    def __setVerified(self, x):
        if type(x) == bool:
            self.__verified = x
        else:
            raise ValueError(x, self.__getStr('boolE'))

    def __setPixmap(self, x):
        if isinstance(x, QPixmap):
            self.__pixmap = x
        else:
            raise ValueError(x, self.__getStr('pixmapE'))

    def __setShapes(self, x):
        self.__shapes = x


    ###########################################################################
    #                           P R O P E R T I E S                           #
    ###########################################################################

    verified = property(__getVerified, __setVerified)
    pixmap = property(__getPixmap, __setPixmap)
    shapes = property(__getShapes, __setShapes)