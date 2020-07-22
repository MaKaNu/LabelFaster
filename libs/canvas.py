from re import sub
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from libs.stringBundle import StringBundle
from libs.shape import Shape
from libs.utils import distance
from libs.errors import *

CURSOR_DEFAULT = Qt.ArrowCursor
CURSOR_POINT = Qt.PointingHandCursor
CURSOR_DRAW = Qt.CrossCursor
CURSOR_MOVE = Qt.ClosedHandCursor
CURSOR_GRAB = Qt.OpenHandCursor


class Canvas(QWidget):
    CREATE, EDIT = list(range(2))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__pixmap = QPixmap()
        self.__mode = self.EDIT
        self.__current = None
        self.__shapes = []
        self.__verified = False
        self.scale = 1.0
        self._painter = QPainter()
        self._cursor = CURSOR_DEFAULT

        # Load string bundle for i18n
        self.__stringBundle = StringBundle.getBundle()

        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.WheelFocus)

    def loadPixmap(self, pixmap):
        self.pixmap = pixmap
        self.shapes = []
        self.repaint()

    ###########################################################################
    #                                 E D I T                                 #
    ###########################################################################

    def setEditing(self, value=True):
        self.mode = self.EDIT if value else self.CREATE

    def drawing(self):
        return self.mode == self.CREATE

    def editing(self):
        return self.mode == self.EDIT

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

        # Polygon drawing.
        if self.drawing():
            self.overrideCursor(CURSOR_DRAW)
            if self.current:
                # Display annotation width and height while drawing
                currentWidth = abs(self.current[0].x() - pos.x())
                currentHeight = abs(self.current[0].y() - pos.y())
                self.parent().window().labelCoordinates.setText(
                        'Width: %d, Height: %d / X: %d; Y: %d' % (
                            currentWidth,
                            currentHeight,
                            pos.x(), pos.y()))

        # Action if left button and controll are set
        # needs to be implemented.
        if Qt.LeftButton & ev.buttons()\
                and Qt.ControlModifier & ev.modifiers():
            pass

        # Action if right button and controll are set
        # needs to be implemented.
        if Qt.RightButton & ev.buttons()\
                and Qt.ControlModifier & ev.modifiers():
            pass

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
            if (shape.selected or not self._hideBackround) \
                    and self.isVisible(shape):
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

    def __getMode(self):
        return self.__mode

    def __getCurrent(self):
        return self.__current

    ###########################################################################
    #                               S E T T E R                               #
    ###########################################################################

    def __setVerified(self, x):
        if isinstance(x, bool):
            self.__verified = x
        else:
            raise ValueError(x, self.__getStr('verifiedE'))

    def __setPixmap(self, x):
        if isinstance(x, QPixmap):
            self.__pixmap = x
        else:
            raise ValueError(x, self.__getStr('pixmapE'))

    def __setShapes(self, x):
        self.__shapes = x

    def __setMode(self, x):
        if isinstance(x, int) and x == 1 or x == 0:
            self.__mode = x
        else:
            raise ValueError(x, self.__getStr('modeE'))

    def __setCurrent(self, x):
        if isinstance(x, Shape):
            self.__mode = x
        else:
            raise ValueError(x, self.__getStr('currentE'))

    ###########################################################################
    #                           P R O P E R T I E S                           #
    ###########################################################################

    verified = property(__getVerified, __setVerified)
    pixmap = property(__getPixmap, __setPixmap)
    shapes = property(__getShapes, __setShapes)
    mode = property(__getMode, __setMode)
    current = property(__getCurrent, __setCurrent)
