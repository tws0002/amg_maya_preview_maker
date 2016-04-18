from PySide.QtCore import *
from PySide.QtGui import *
from ..renderer import frame_stamp
reload(frame_stamp)
from pymel.core import *
import os

class PreviewWidget(QWidget):
    padding = 20
    bg = (20,20,20)
    closeSignal = Signal(object)
    def __init__(self, image_path=None, remove_on_load=False, data=None, add_stamp=True, parent=None):
        super(PreviewWidget, self).__init__(parent)
        self.setWindowFlags(Qt.Tool)
        # self.resize(800, 600)
        self.data = data
        self.image = image_path
        self.remove_on_load = remove_on_load
        self.setAcceptDrops(True)
        self.setMinimumHeight(self.padding*3)
        self.setMinimumWidth(self.padding*3)
        self.pixmap = None
        self.update_image(self.image, add_stamp=add_stamp)
        if self.pixmap:
            width =  self.pixmap.rect().size().width()
            height = self.pixmap.rect().size().height()
            w = min(width,800)
            h = int(w*(height/float(width)))
            self.resize(w+10, h+10)
            geo = self.geometry()
            geo.moveCenter(parent.geometry().center())
            self.setGeometry(geo)
        self.updateTitle()

    def closeEvent(self, event):
        self.closeSignal.emit(self.geometry())
        if self.remove_on_load:
            os.remove(self.image)
        super(PreviewWidget, self).closeEvent(event)

    def update_image(self, path=None, add_stamp=True):
        if path or self.image:
            if add_stamp:
                # stamp = frame_stamp.set_frame_number(self.data['stamp'] or frame_stamp.data_example, int(getCurrentTime())) or self.data['stamp']
                # self.pixmap = frame_stamp.add_stamp(stamp,
                #                                     image_path=path or self.image, qtpixmap=1, bg_color=tuple(self.data['bg_color']),
                #                                     font_size=self.data['font_size'], font=self.data['font'], backdrop=self.data.get('backdrop',True))
                self.pixmap = self.get_stamped_pixmap(path or self.image, self.data, int(getCurrentTime()))
            else:
                self.pixmap = QPixmap(path or self.image)
        else:
            defimage = frame_stamp.default_image(w=800, h=600, checkersize=50)
            if add_stamp:
                self.pixmap = frame_stamp.add_stamp(self.data['stamp'] or frame_stamp.data_example, raw_image=defimage,
                                                    qtpixmap=1, bg_color=tuple(self.data['bg_color']),
                                                    font_size=self.data['font_size'], font=self.data['font'], backdrop=self.data.get('backdrop',True))
            else:
                self.pixmap = defimage
        self.update()

    @staticmethod
    def get_stamped_pixmap(path, data, frame=0):
        stamp = frame_stamp.set_frame_number(data.get('stamp') or frame_stamp.data_example, frame) or (data.get('stamp') or frame_stamp.data_example)
        pix = frame_stamp.add_stamp(stamp, image_path=path, qtpixmap=True, bg_color=tuple(data['bg_color']),
                             font_size=data['font_size'], font=data['font'], backdrop=data.get('backdrop',True))
        return pix

    def update_stamp(self, data, add_stamp):
        self.data = data
        self.update_image(add_stamp=add_stamp)

    def paintEvent(self, event):
        p = QPainter()
        p.begin(self)
        p.setRenderHint(QPainter.HighQualityAntialiasing, True)
        rec = self.visibleRegion().boundingRect()
        # bg
        p.setBrush(QBrush(QColor(*self.bg)))
        p.drawRect(rec)
        # pixmap
        scaleRect = self.pixmap.rect().intersected(rec)#.adjusted(self.padding, self.padding, -self.padding, -self.padding))
        if not scaleRect == self.pixmap.rect():
            pix = self.pixmap.scaled(scaleRect.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            pix = self.pixmap
        pixRec = pix.rect()
        pixRec.moveCenter(rec.center())
        p.drawPixmap(pixRec, pix)
        self.updateTitle(scaleRect.height())
        p.end()

    def dragEnterEvent(self, event):
        event.acceptProposedAction()
        super(PreviewWidget, self).dragEnterEvent(event)

    def dragMoveEvent(self, event):
        event.acceptProposedAction()
        super(PreviewWidget, self).dragMoveEvent(event)

    def dropEvent(self, event):
        event.acceptProposedAction()
        event.accept()
        if  event.mimeData().hasUrls():
            mim = event.mimeData()
            urls = mim.urls()
            path = urls[0].toLocalFile()
            self.update_image(path)

    def updateTitle(self, scale=None):
        postfix = ''
        if scale and self.pixmap:
            s = float(scale) / self.pixmap.size().height()
            if s < 1:
                postfix = '  %s%%' % int(s*100)
        self.setWindowTitle('Frame Stamp Preview' + postfix)
