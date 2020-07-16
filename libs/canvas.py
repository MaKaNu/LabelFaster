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
    #                                 E D I T                                 #
    ###########################################################################

    def setEditing(self, value=True):
        self.mode = self.EDIT if value else self.CREATE

    ###########################################################################
    #                                P O S E S                                #
    ###########################################################################

    def transformPos(self, point):
        # Convert from widget-logical coord to painter-logical coord.
        return point / self.scale - self.offsetToCenter()

    def offsetToCenter(self):
        s = self.scale
        area = super(Canvas, self).size()
        w, h = self.pixmap.width() * s, self.pixmap.height() * s
        aw, ah = area.width(), area.height()
        x = (aw - w) / (2 * s) if aw > w else 0
        y = (ah - h) / (2 * s) if ah > h else 0
        return QPointF(x, y)

    ###########################################################################
    #                               C U R S O R                               #
    ###########################################################################

    def currentCursor(self):
        cursor = QApplication.overrideCursor()
        if cursor is not None:
            cursor = cursor.shape()
        return cursor

    def overrideCursor(self, cursor):
        self._cursor = cursor
        if self.currentCursor() is None:
            QApplication.setOverrideCursor(cursor)
        else:
            QApplication.changeOverrideCursor(cursor)

    def restoreCursor(self):
        QApplication.restoreOverrideCursor()

    def outOfPixmap(self, p):
        w, h = self.pixmap.width(), self.pixmap.height()
        return not (0 <= p.x() <= w and 0 <= p.y() <= h)

    ###########################################################################
    #                               E V E N T S                               #
    ###########################################################################

    def enterEvent(self, ev):
        self.overrideCursor(self._cursor)

    def leaveEvent(self, ev):
        self.restoreCursor()

    def mouseMoveEvent(self, ev):
        """Update line with last point and current coordinates."""
        pos = self.transformPos(ev.pos())

        # Update coordinates in status bar if image is opened
        window = self.parent().window()
        if window.filePath is not None:
            self.parent().window().labelCoordinates.setText(
                'X: %d; Y: %d' % (pos.x(), pos.y()))

    def paintEvent(self, event):
        if not self.pixmap:
            return super(Canvas, self).paintEvent(event)

        p = self._painter
        p.begin(self)
        # #^^vv^^vv^^vv^^vv^^vv^^vv^^vv^^vv^^vv^^vv^^vv^^vv^^vv^^vv^^vv^^vv^# #
        # --------------------------- begin paint --------------------------- #
        # #^^vv^^vv^^vv^^vv^^vv^^vv^^vv^^vv^^vv^^vv^^vv^^vv^^vv^^vv^^vv^^vv^# #
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.HighQualityAntialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)

        p.scale(self.scale, self.scale)
        p.translate(self.offsetToCenter())

        p.drawPixmap(0, 0, self.pixmap)

        Shape.scale = self.scale
        for shape in self.shapes:
            if (shape.selected or not self._hideBackround) and self.isVisible(shape):
                shape.fill = shape.selected or shape == self.hShape
                shape.paint(p)
        # #^^vv^^vv^^vv^^vv^^vv^^vv^^vv^^vv^^vv^^vv^^vv^^vv^^vv^^vv^^vv^^vv^# #
        # ---------------------------- end paint ---------------------------- #
        # #^^vv^^vv^^vv^^vv^^vv^^vv^^vv^^vv^^vv^^vv^^vv^^vv^^vv^^vv^^vv^^vv^# #
        p.end()

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
