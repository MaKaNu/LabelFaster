from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from libs.stringBundle import StringBundle
from libs.errors import *

class Canvas(QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__pixmap = QPixmap()
        self.__verified = False

        # Load string bundle for i18n
        self.__stringBundle = StringBundle.getBundle()

    ###########################################################################
    #                               G E T T E R                               #
    ###########################################################################

    def __getStr(self, strId):
        return self.__stringBundle.getString(strId)

    def __getVerified(self):
        return self.__verified

    def __getPixmap(self):
        return self.__pixmap

    ###########################################################################
    #                               S E T T E R                               #
    ###########################################################################

    def __setVerified(self, x):
        if type(x) == bool:
            self.__verified = x
        else:
            warn(self.__getStr('warnBool'))

    ###########################################################################
    #                           P R O P E R T I E S                           #
    ###########################################################################

    verified = property(__getVerified, __setVerified)
    pixmap = property(__getPixmap)
