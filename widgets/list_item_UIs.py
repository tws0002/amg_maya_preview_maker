# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\Dropbox\Dropbox\pw_pipeline\pw_pipeline\assets\maya\python\TOOLS\asset_submitter\widgets\list_item.ui'
#
# Created: Fri Dec 25 19:21:20 2015
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_shader_item(object):
    def setupUi(self, shader_item):
        shader_item.setObjectName("shader_item")
        shader_item.resize(375, 70)
        shader_item.setMinimumSize(QtCore.QSize(0, 70))
        shader_item.setMaximumSize(QtCore.QSize(16777215, 70))
        self.horizontalLayout = QtGui.QHBoxLayout(shader_item)
        self.horizontalLayout.setContentsMargins(15, 2, 2, 2)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.use_btn = QtGui.QPushButton(shader_item)
        self.use_btn.setMinimumSize(QtCore.QSize(35, 35))
        self.use_btn.setMaximumSize(QtCore.QSize(35, 35))
        self.use_btn.setCheckable(True)
        self.use_btn.setChecked(True)
        self.use_btn.setObjectName("use_btn")
        self.horizontalLayout.addWidget(self.use_btn)
        self.name_lb = QtGui.QLabel(shader_item)
        self.name_lb.setObjectName("name_lb")
        self.horizontalLayout.addWidget(self.name_lb)
        self.preview_ly = QtGui.QHBoxLayout()
        self.preview_ly.setObjectName("preview_ly")
        self.horizontalLayout.addLayout(self.preview_ly)
        self.horizontalLayout.setStretch(1, 1)

        self.retranslateUi(shader_item)
        QtCore.QMetaObject.connectSlotsByName(shader_item)

    def retranslateUi(self, shader_item):
        shader_item.setWindowTitle(QtGui.QApplication.translate("shader_item", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.use_btn.setText(QtGui.QApplication.translate("shader_item", "ON", None, QtGui.QApplication.UnicodeUTF8))
        self.name_lb.setText(QtGui.QApplication.translate("shader_item", "Shader Name", None, QtGui.QApplication.UnicodeUTF8))

