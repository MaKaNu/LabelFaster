from PyQt5.QtWidgets import QMessageBox


def discardChangesDialog(parent):
    yes, no = QMessageBox.Yes, QMessageBox.No
    msg = u'You have unsaved changes, proceed anyway?'
    return yes == QMessageBox.warning(parent, u'Attention', msg, yes | no)


def errorMessage(parent, title, message):
    return QMessageBox.critical(parent, title,
                                '<p><b>%s</b></p>%s' % (title, message))


def noClassMessage(parent):
    title = u'No Class Selected'
    msg = 'No Active Class Selected.'
    msgDetail = 'Please choose your active class by clicking on the ' + \
        'buttons in the class toolbar or use the associated shortcut.'
    msgBox = QMessageBox.warning(
        parent,
        title,
        '<p><b>%s</b></p>%s' % (msg, msgDetail),
        QMessageBox.Ok)
    return msgBox
