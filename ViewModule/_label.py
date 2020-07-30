from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QColor

from libs.utils import generateColorByText
from libs.shape import Shape
from libs.hashableQListWidgetItem import HashableQListWidgetItem


def addLabel(self, shape):
    # shape.paintLabel = self.displayLabelOption.isChecked()
    item = HashableQListWidgetItem(shape.label)
    item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
    item.setCheckState(Qt.Checked)
    item.setBackground(generateColorByText(shape.label))
    self.itemsToShapes[item] = shape
    self.shapesToItems[shape] = item
    self.labelList.addItem(item)
    for action in self.actions.onShapesPresent:
        action.setEnabled(True)


def remLabel(self, shape):
    if shape is None:
        # print('rm empty label')
        return
    item = self.shapesToItems[shape]
    self.labelList.takeItem(self.labelList.row(item))
    del self.shapesToItems[shape]
    del self.itemsToShapes[item]


def loadLabels(self, shapes):
    s = []
    for label, points, line_color, fill_color, difficult in shapes:
        shape = Shape(label=label)
        for x, y in points:

            # Ensure the labels are within the bounds of the image.
            # If not, fix them.
            x, y, snapped = self.canvas.snapPointToCanvas(x, y)
            if snapped:
                self.setDirty()

            shape.addPoint(QPointF(x, y))
        shape.difficult = difficult
        shape.close()
        s.append(shape)

        if line_color:
            shape.line_color = QColor(*line_color)
        else:
            shape.line_color = generateColorByText(label)

        if fill_color:
            shape.fill_color = QColor(*fill_color)
        else:
            shape.fill_color = generateColorByText(label)

        self.addLabel(shape)
    self.canvas.loadShapes(s)


"""
def saveLabels(self, annotationFilePath):
    if self.labelFile is None:
        self.labelFile = LabelFile()
        self.labelFile.verified = self.canvas.verified

    def format_shape(s):
        return dict(label=s.label,
                    line_color=s.line_color.getRgb(),
                    fill_color=s.fill_color.getRgb(),
                    points=[(p.x(), p.y()) for p in s.points]
                    )

    shapes = [format_shape(shape) for shape in self.canvas.shapes]
    # Can add differrent annotation formats here
    try:
        if self.usingPascalVocFormat is True:
            if annotationFilePath[-4:].lower() != ".xml":
                annotationFilePath += XML_EXT
            self.labelFile.savePascalVocFormat(annotationFilePath, shapes, self.filePath, self.imageData,
                                                self.lineColor.getRgb(), self.fillColor.getRgb())
        elif self.usingYoloFormat is True:
            if annotationFilePath[-4:].lower() != ".txt":
                annotationFilePath += TXT_EXT
            self.labelFile.saveYoloFormat(annotationFilePath, shapes, self.filePath, self.imageData, self.labelHist,
                                                self.lineColor.getRgb(), self.fillColor.getRgb())
        else:
            self.labelFile.save(annotationFilePath, shapes, self.filePath, self.imageData,
                                self.lineColor.getRgb(), self.fillColor.getRgb())
        print('Image:{0} -> Annotation:{1}'.format(self.filePath, annotationFilePath))
        return True
    except LabelFileError as e:
        self.errorMessage(u'Error saving label data', u'<b>%s</b>' % e)
        return False
"""
