from PyQt5.QtWidgets import QMessageBox


def discardChangesDialog(parent):
    yes, no = QMessageBox.Yes, QMessageBox.No
    msg = u'You have unsaved changes, proceed anyway?'
    return yes == QMessageBox.warning(parent, u'Attention', msg, yes | no)


def errorMessage(parent, title, message):
    return QMessageBox.critical(parent, title,
                                '<p><b>%s</b></p>%s' % (title, message))
