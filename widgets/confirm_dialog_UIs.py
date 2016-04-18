# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\work\amg\amg_pipeline\scripts\maya\python\Tools\asset_submitter\widgets\confirm_dialog.ui'
#
# Created: Sat Mar 05 14:15:09 2016
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_confirm(object):
    def setupUi(self, confirm):
        confirm.setObjectName("confirm")
        confirm.resize(994, 727)
        self.verticalLayout = QtGui.QVBoxLayout(confirm)
        self.verticalLayout.setObjectName("verticalLayout")
        self.view = QtWebKit.QWebView(confirm)
        self.view.setUrl(QtCore.QUrl("about:blank"))
        self.view.setObjectName("view")
        self.verticalLayout.addWidget(self.view)
        self.continue_btn = QtGui.QPushButton(confirm)
        self.continue_btn.setMinimumSize(QtCore.QSize(0, 40))
        font = QtGui.QFont()
        font.setPointSize(11)
        font.setWeight(75)
        font.setBold(True)
        self.continue_btn.setFont(font)
        self.continue_btn.setObjectName("continue_btn")
        self.verticalLayout.addWidget(self.continue_btn)

        self.retranslateUi(confirm)
        QtCore.QMetaObject.connectSlotsByName(confirm)

    def retranslateUi(self, confirm):
        confirm.setWindowTitle(QtGui.QApplication.translate("confirm", "Cunfirm Submit", None, QtGui.QApplication.UnicodeUTF8))
        self.continue_btn.setText(QtGui.QApplication.translate("confirm", "Continue", None, QtGui.QApplication.UnicodeUTF8))

from PySide import QtWebKit
