from PySide.QtCore import *
from PySide.QtGui import *
from pymel.core import *
import list_item_UIs
reload(list_item_UIs)
import shader_manager
reload(shader_manager)
from .. import submitter_variables as v
reload(v)
from ..tools import shaders, camera_rig
from ..icons.icons import icons
reload(shaders)
import os, json


class ShaderListClass(QListWidget):
    def __init__(self, type, parent):
        super(ShaderListClass, self).__init__()
        self.type = type
        self.par = parent
        self.setMinimumHeight(200)
        self.setStyleSheet("QListWidget::item{ height: 70px; font-size:16;}")
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)

        self.select_default_layer()
        self.currentItemChanged.connect(self.switch_selected_layer)
        self.itemClicked.connect(self.switch_selected_layer)
        QTimer.singleShot(500, self.refresh_list)

    def select_default_layer(self):
        self.setCurrentRow(0)

    def refresh_list(self):
        self.clear()
        for x in shaders.shaders[self.type]:
            self.add_shader(x)

    def check_list(self):
        for i in range(self.count()):
            self.itemWidget(self.item(i)).check_layer()

    def add_shader(self, data):
        item =  QListWidgetItem(self)
        w = ListItem(data, item, self)
        w.selectMe.connect(self.setCurrentItem)
        w.goToDefaultSignal.connect(self.select_default_layer)
        self.setItemWidget(item, w)
        self.addItem(item)

    def switch_selected_layer(self, current=None, previous=None):
        if previous:
            previous = self.itemWidget(previous)
        # sel = self.selectedItems()
        current = current or (self.selectedItems() or [None])[0]
        if current:
            w = self.itemWidget(current)
            w.update_layer(previous)

    def update_objects_in_layers(self):
        for i in range(self.count()):
            self.itemWidget(self.item(i)).update_layer_objects()

    def rebuild_layers(self):
        for i in range(self.count()):
            self.itemWidget(self.item(i)).rebuild_layer()

    def wheelEvent(self, event):
        inc = 15
        if QApplication.keyboardModifiers() == Qt.ControlModifier:
            inc = 50
        if event.delta() > 0:
            self.verticalScrollBar().setValue(self.verticalScrollBar().value()-inc)
        else:
            self.verticalScrollBar().setValue(self.verticalScrollBar().value()+inc)
        # super(ShaderListClass, self).wheelEvent(event)

class ListItem(QWidget, list_item_UIs.Ui_shader_item):
    selectMe = Signal(object)
    goToDefaultSignal = Signal()
    def __init__(self, data, item, parent):
        super(ListItem, self).__init__()
        self.setupUi(self)
        self.item = item
        self.par = parent
        self.use_btn.setText('')
        self.use_btn.setIconSize(QSize(32,32))
        self.name_lb.setText(data['title'] + ' (%s)' % data['func'].shader_name)
        self.manager = data['func']()
        if False:
            self.manager = shaders.LayerManager()

        preview = v.join(v.preview_images, self.manager.preview_name())

        if not os.path.exists(preview):
            preview = v.join(v.preview_images, 'default.png').replace('\\','/')
        if os.path.exists(preview):
            prew = QLabel(self)
            prew.setFixedSize(QSize(65,65))
            pix = QPixmap(preview).scaled(65, 65, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            prew.setPixmap(pix)
            self.preview_ly.addWidget(prew)

        if not self.manager.get_shader() and not self.manager.shader_name == 'original':
            self.name_lb.setStyleSheet('color:orange;')
            self.use_btn.setEnabled(0)        #connect

        self.use_btn.setChecked(bool(self.manager.layer))
        self.use_btn.setIcon(QIcon(icons['checked'] if bool(self.manager.layer) else icons['unchecked']))
        self.use_btn.clicked.connect(self.on_off)

    def on_off(self):
        if self.use_btn.isChecked():
            self.use_btn.setIcon(QIcon(icons['checked']))
            self.create_layer()
            self.selectMe.emit(self.item)
        else:
            self.use_btn.setIcon(QIcon(icons['unchecked']))
            self.manager.remove_layer()
            self.goToDefaultSignal.emit()

    def create_layer(self):
        self.manager.create_layer()
        render = self.par.par.render_objects()
        shade = self.par.par.shaded_objects()
        self.manager.update_layer_objects(render, shade)

    def update_layer(self, prev):
        if self.use_btn.isChecked():
            if prev:
                prev.disable_layer()
            self.manager.update_layer()

    def disable_layer(self):
        if self.use_btn.isChecked():
            self.manager.disable_layer()

    def update_layer_objects(self):
        render = self.par.par.render_objects()
        shade = self.par.par.shaded_objects()
        self.manager.update_layer_objects(render, shade)

    def rebuild_layer(self):
        self.manager.remove_layer()
        if self.use_btn.isChecked():
            self.create_layer()

    def check_layer(self):
        if self.use_btn.isChecked():
            if not objExists(self.manager.layer):
                self.manager.create_layer()
                # self.manager.create_layer()






