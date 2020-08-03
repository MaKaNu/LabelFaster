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
    drawingPolygon = pyqtSignal(bool)
    newShape = pyqtSignal()

    CREATE, EDIT = list(range(2))

    epsilon = 11.0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__pixmap = QPixmap()
        self.__mode = self.EDIT
        self.__current = None
        self.__hShape = None
        self.__hVertex = None
        self.__shapes = []
        self.__drawingLineColor = QColor(45, 168, 179)
        self.__drawingRectColor = QColor(45, 168, 179)
        self.__line = Shape(line_color=self.drawingLineColor)
        self.__selectedShape = None
        self.__verified = False
        self.__hideBackground = False
        self.__visible = {}
        self.scale = 1.0
        self._painter = QPainter()
        self._cursor = CURSOR_DEFAULT

        # Load string bundle for i18n
        self.__stringBundle = StringBundle.getBundle()

        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.WheelFocus)

    ###########################################################################
    #                                S T A T E                                #
    ###########################################################################

    def resetState(self):
        self.restoreCursor()
        self.pixmap = None
        self.update()

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
    #                               S H A P E S                               #
    ###########################################################################

    def selectShape(self, shape):
        self.deSelectShape()
        shape.selected = True
        self.selectedShape = shape
        self.setHiding()
        self.selectionChanged.emit(True)
        self.update()

    def selectShapePoint(self, point):
        """Select the first shape created which contains this point."""
        self.deSelectShape()
        if self.selectedVertex():  # A vertex is marked for selection.
            index, shape = self.hVertex, self.hShape
            shape.highlightVertex(index, shape.MOVE_VERTEX)
            self.selectShape(shape)
            return
        for shape in reversed(self.shapes):
            if self.isVisible(shape) and shape.containsPoint(point):
                self.selectShape(shape)
                self.calculateOffsets(shape, point)
                return

    def deSelectShape(self):
        if self.selectedShape:
            self.selectedShape.selected = False
            self.selectedShape = None
            self.setHiding(False)
            self.selectionChanged.emit(False)
            self.update()

    def selectedVertex(self):
        return self.hVertex is not None

    ###########################################################################
    #                              D R A W I N G                              #
    ###########################################################################

    def loadPixmap(self, pixmap):
        self.pixmap = pixmap
        self.shapes = []
        self.repaint()

    def loadShapes(self, shapes):
        self.shapes = list(shapes)
        self.current = None
        self.repaint()

    def handleDrawing(self, pos):
        if self.current and self.current.reachMaxPoints() is False:
            initPos = self.current[0]
            minX = initPos.x()
            minY = initPos.y()
            targetPos = self.line[1]
            maxX = targetPos.x()
            maxY = targetPos.y()
            self.current.addPoint(QPointF(maxX, minY))
            self.current.addPoint(targetPos)
            self.current.addPoint(QPointF(minX, maxY))
            self.finalise()
        elif not self.outOfPixmap(pos):
            self.current = Shape()
            self.current.addPoint(pos)
            self.line.points = [pos, pos]
            # self.setHiding()
            self.drawingPolygon.emit(True)
            self.update()

    # def setHiding(self, enable=True):
        # self._hideBackround = self.hideBackround if enable else False

    def finalise(self):
        assert self.current
        if self.current.points[0] == self.current.points[-1]:
            self.current = None
            self.drawingPolygon.emit(False)
            self.update()
            return
        self.current.close()
        self.shapes.append(self.current)
        self.current = None
        self.hideBackground = False
        self.newShape.emit()
        self.update()

    def undoLastLine(self):
        assert self.shapes
        self.current = self.shapes.pop()
        self.current.setOpen()
        self.line.points = [self.current[-1], self.current[0]]
        self.drawingPolygon.emit(True)

    def resetAllLines(self):
        assert self.shapes
        self.current = self.shapes.pop()
        self.current.setOpen()
        self.line.points = [self.current[-1], self.current[0]]
        self.drawingPolygon.emit(True)
        self.current = None
        self.drawingPolygon.emit(False)
        self.update()

    def closeEnough(self, p1, p2):
        return distance(p1 - p2) < self.epsilon

    def isVisible(self, shape):
        return self.visible.get(shape, True)

    def setDrawingColor(self, qColor):
        self.drawingLineColor = qColor
        self.drawingRectColor = qColor

    def snapPointToCanvas(self, x, y):
        """
        Moves a point x,y to within the boundaries of the canvas.
        :return: (x,y,snapped) where snapped is True if x or y were changed,
        False if not.
        """
        if x < 0 or x > self.pixmap.width() or \
           y < 0 or y > self.pixmap.height():
            x = max(x, 0)
            y = max(y, 0)
            x = min(x, self.pixmap.width())
            y = min(y, self.pixmap.height())
            return x, y, True

        return x, y, False

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

                color = self.drawingLineColor
                if self.outOfPixmap(pos):
                    # Don't allow the user to draw outside the pixmap.
                    # Clip the coordinates to 0 or max,
                    # if they are outside the range [0, max]
                    size = self.pixmap.size()
                    clipped_x = min(max(0, pos.x()), size.width())
                    clipped_y = min(max(0, pos.y()), size.height())
                    pos = QPointF(clipped_x, clipped_y)
                elif len(self.current) > 1 and \
                        self.closeEnough(pos, self.current[0]):
                    # Attract line to starting point and colorise to alert the
                    # user:
                    pos = self.current[0]
                    color = self.current.line_color
                    self.overrideCursor(CURSOR_POINT)
                    self.current.highlightVertex(0, Shape.NEAR_VERTEX)

                # if self.drawSquare:
                if False:
                    initPos = self.current[0]
                    minX = initPos.x()
                    minY = initPos.y()
                    min_size = min(abs(pos.x() - minX), abs(pos.y() - minY))
                    directionX = -1 if pos.x() - minX < 0 else 1
                    directionY = -1 if pos.y() - minY < 0 else 1
                    self.line[1] = QPointF(
                        minX + directionX * min_size,
                        minY + directionY * min_size)
                else:
                    self.line[1] = pos

                self.line.line_color = color
                self.prevPoint = QPointF()
                self.current.highlightClear()
            else:
                self.prevPoint = pos
            self.repaint()
            return

        # Polygon copy moving.
        if Qt.RightButton & ev.buttons():
            if self.selectedShapeCopy and self.prevPoint:
                self.overrideCursor(CURSOR_MOVE)
                self.boundedMoveShape(self.selectedShapeCopy, pos)
                self.repaint()
            elif self.selectedShape:
                self.selectedShapeCopy = self.selectedShape.copy()
                self.repaint()
            return

        # Polygon/Vertex moving.
        if Qt.LeftButton & ev.buttons():
            if self.selectedVertex():
                self.boundedMoveVertex(pos)
                self.shapeMoved.emit()
                self.repaint()
            elif self.selectedShape and self.prevPoint:
                self.overrideCursor(CURSOR_MOVE)
                self.boundedMoveShape(self.selectedShape, pos)
                self.shapeMoved.emit()
                self.repaint()
            return

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

    def mousePressEvent(self, ev):
        pos = self.transformPos(ev.pos())

        if Qt.LeftButton & ev.buttons():
            if self.drawing():
                self.handleDrawing(pos)
            else:
                self.selectShapePoint(pos)
                self.prevPoint = pos
                self.repaint()
        else:
            pass

    def mouseReleaseEvent(self, ev):
        if Qt.RightButton == ev.button():
            # menu = self.menus[bool(self.selectedShapeCopy)]
            # self.restoreCursor()
            # if not menu.exec_(self.mapToGlobal(ev.pos()))\
            #    and self.selectedShapeCopy:
            #     # Cancel the move by deleting the shadow copy.
            #     self.selectedShapeCopy = None
            #     self.repaint()
            pass
        elif Qt.LeftButton == ev.button() and self.selectedShape:
            if self.selectedVertex():
                self.overrideCursor(CURSOR_POINT)
            else:
                self.overrideCursor(CURSOR_GRAB)
        elif Qt.LeftButton == ev.button():
            pos = self.transformPos(ev.pos())
            if self.drawing():
                self.handleDrawing(pos)

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
            if (shape.selected or not self.hideBackground) \
                    and self.isVisible(shape):
                shape.fill = shape.selected or shape == self.hShape
                shape.paint(p)
        if self.current:
            self.current.paint(p)
            self.line.paint(p)
        # if self.selectedShapeCopy:
            # self.selectedShapeCopy.paint(p)

        # Paint rect
        if self.current is not None and len(self.line) == 2:
            leftTop = self.line[0]
            rightBottom = self.line[1]
            rectWidth = rightBottom.x() - leftTop.x()
            rectHeight = rightBottom.y() - leftTop.y()
            p.setPen(self.drawingRectColor)
            brush = QBrush(Qt.BDiagPattern)
            p.setBrush(brush)
            p.drawRect(leftTop.x(), leftTop.y(), rectWidth, rectHeight)

        if self.drawing() and not self.prevPoint.isNull() \
                and not self.outOfPixmap(self.prevPoint):
            p.setPen(QColor(0, 0, 0))
            p.drawLine(
                self.prevPoint.x(), 0,
                self.prevPoint.x(), self.pixmap.height())
            p.drawLine(
                0, self.prevPoint.y(),
                self.pixmap.width(), self.prevPoint.y())

        self.setAutoFillBackground(True)
        if self.verified:
            pal = self.palette()
            pal.setColor(self.backgroundRole(), QColor(184, 239, 38, 128))
            self.setPalette(pal)
        else:
            pal = self.palette()
            pal.setColor(self.backgroundRole(), QColor(232, 232, 232, 255))
            self.setPalette(pal)
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

    def __getLine(self):
        return self.__line

    def __getDrawingLineColor(self):
        return self.__drawingLineColor

    def __getDrawingRectColor(self):
        return self.__drawingRectColor

    def __getSelectedShape(self):
        return self.__selectedShape

    def __getHideBackground(self):
        return self.__hideBackground

    def __getVisible(self):
        return self.__visible

    def __getHShape(self):
        return self.__hShape

    def __getHVertex(self):
        return self.__hVertex

    ###########################################################################
    #                               S E T T E R                               #
    ###########################################################################

    def setLastLabel(self, text, line_color=None, fill_color=None):
        assert text
        self.shapes[-1].label = text
        if line_color:
            self.shapes[-1].line_color = line_color

        if fill_color:
            self.shapes[-1].fill_color = fill_color

        return self.shapes[-1]

    def __setVerified(self, x):
        if isinstance(x, bool):
            self.__verified = x
        else:
            raise ValueError(x, self.__getStr('boolE'))

    def __setPixmap(self, x):
        if isinstance(x, QPixmap) or x is None:
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
        if isinstance(x, Shape) or x is None:
            self.__current = x
        else:
            raise ValueError(x, self.__getStr('shapeE'))

    def __setLine(self, x):
        if isinstance(x, Shape) or x is None:
            self.__line = x
        else:
            raise ValueError(x, self.__getStr('shapeE'))

    def __setdrawingLineColor(self, x):
        if isinstance(x, QColor):
            self.__drawingLineColor = x
        else:
            raise ValueError(x, self.__getStr('colorE'))

    def __setdrawingRectColor(self, x):
        if isinstance(x, QColor):
            self.__drawingRectColor = x
        else:
            raise ValueError(x, self.__getStr('colorE'))

    def __setSelectedShape(self, x):
        if isinstance(x, Shape) or x is None:
            self.__selectedShape = x
        else:
            raise ValueError(x, self.__getStr('shapeE'))

    def __setHideBackground(self, x):
        if isinstance(x, bool):
            self.__hideBackground = x
        else:
            raise ValueError(x, self.__getStr('boolE'))

    def __setVisible(self, x):
        if isinstance(x, bool):
            self.__visible = x
        else:
            raise ValueError(x, self.__getStr('dictE'))

    def __setHShape(self, x):
        if isinstance(x, Shape):
            self.__hShape = x
        else:
            raise ValueError(x, self.__getStr('shapeE'))

    def __setHVertex(self, x):
        if isinstance(x, int):
            self.__hVertex = x
        else:
            raise ValueError(x, self.__getStr('intE'))
    ###########################################################################
    #                           P R O P E R T I E S                           #
    ###########################################################################

    verified = property(__getVerified, __setVerified)
    pixmap = property(__getPixmap, __setPixmap)
    shapes = property(__getShapes, __setShapes)
    mode = property(__getMode, __setMode)
    current = property(__getCurrent, __setCurrent)
    line = property(__getLine, __setLine)
    drawingLineColor = property(__getDrawingLineColor, __setdrawingLineColor)
    drawingRectColor = property(__getDrawingRectColor, __setdrawingRectColor)
    selectedShape = property(__getSelectedShape, __setSelectedShape)
    hideBackground = property(__getHideBackground, __setHideBackground)
    visible = property(__getVisible, __setVisible)
    hShape = property(__getHShape, __setHShape)
    hVertex = property(__getHVertex, __setHVertex)
