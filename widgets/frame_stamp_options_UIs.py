# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\work\amg\amg_pipeline\scripts\maya\python\tools\asset_submitter\widgets\frame_stamp_options.ui'
#
# Created: Sun Apr 03 23:49:31 2016
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_Stamp_Options(object):
    def setupUi(self, Stamp_Options):
        Stamp_Options.setObjectName("Stamp_Options")
        Stamp_Options.resize(414, 111)
        self.gridLayout = QtGui.QGridLayout(Stamp_Options)
        self.gridLayout.setObjectName("gridLayout")
        self.opacity_lb = QtGui.QLabel(Stamp_Options)
        self.opacity_lb.setAlignment(QtCore.Qt.AlignCenter)
        self.opacity_lb.setObjectName("opacity_lb")
        self.gridLayout.addWidget(self.opacity_lb, 0, 2, 1, 1)
        self.opacity_sld = QtGui.QSlider(Stamp_Options)
        self.opacity_sld.setMaximum(100)
        self.opacity_sld.setProperty("value", 70)
        self.opacity_sld.setOrientation(QtCore.Qt.Horizontal)
        self.opacity_sld.setObjectName("opacity_sld")
        self.gridLayout.addWidget(self.opacity_sld, 0, 1, 1, 1)
        self.label = QtGui.QLabel(Stamp_Options)
        self.label.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.font_size_sbx = QtGui.QSpinBox(Stamp_Options)
        self.font_size_sbx.setMaximumSize(QtCore.QSize(50, 16777215))
        self.font_size_sbx.setMinimum(6)
        self.font_size_sbx.setMaximum(48)
        self.font_size_sbx.setProperty("value", 14)
        self.font_size_sbx.setObjectName("font_size_sbx")
        self.gridLayout.addWidget(self.font_size_sbx, 3, 1, 1, 1)
        self.backdrop_cbx = QtGui.QCheckBox(Stamp_Options)
        self.backdrop_cbx.setText("")
        self.backdrop_cbx.setChecked(True)
        self.backdrop_cbx.setObjectName("backdrop_cbx")
        self.gridLayout.addWidget(self.backdrop_cbx, 4, 1, 1, 1)
        self.label_3 = QtGui.QLabel(Stamp_Options)
        self.label_3.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 4, 0, 1, 1)
        self.label_5 = QtGui.QLabel(Stamp_Options)
        self.label_5.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_5.setObjectName("label_5")
        self.gridLayout.addWidget(self.label_5, 3, 0, 1, 1)
        self.label_4 = QtGui.QLabel(Stamp_Options)
        self.label_4.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_4.setObjectName("label_4")
        self.gridLayout.addWidget(self.label_4, 5, 0, 1, 1)
        self.font_path_le = QtGui.QLineEdit(Stamp_Options)
        self.font_path_le.setObjectName("font_path_le")
        self.gridLayout.addWidget(self.font_path_le, 5, 1, 1, 1)
        self.set_font_path_le = QtGui.QPushButton(Stamp_Options)
        self.set_font_path_le.setMaximumSize(QtCore.QSize(30, 16777215))
        self.set_font_path_le.setObjectName("set_font_path_le")
        self.gridLayout.addWidget(self.set_font_path_le, 5, 2, 1, 1)

        self.retranslateUi(Stamp_Options)
        QtCore.QObject.connect(self.opacity_sld, QtCore.SIGNAL("valueChanged(int)"), self.opacity_lb.setNum)
        QtCore.QMetaObject.connectSlotsByName(Stamp_Options)

    def retranslateUi(self, Stamp_Options):
        Stamp_Options.setWindowTitle(QtGui.QApplication.translate("Stamp_Options", "Frame Stapm Options", None, QtGui.QApplication.UnicodeUTF8))
        self.opacity_lb.setText(QtGui.QApplication.translate("Stamp_Options", "0", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("Stamp_Options", "BG Opacity", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("Stamp_Options", "Backdrops", None, QtGui.QApplication.UnicodeUTF8))
        self.label_5.setText(QtGui.QApplication.translate("Stamp_Options", "Font Size", None, QtGui.QApplication.UnicodeUTF8))
        self.label_4.setText(QtGui.QApplication.translate("Stamp_Options", "Font File", None, QtGui.QApplication.UnicodeUTF8))
        self.set_font_path_le.setText(QtGui.QApplication.translate("Stamp_Options", "...", None, QtGui.QApplication.UnicodeUTF8))

