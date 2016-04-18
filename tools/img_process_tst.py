from PySide.QtCore import *
from PySide.QtGui import *
import frame_stamp



class PreviewWidget(QWidget):
    padding = 20
    bg = (50,50,50)
    def __init__(self):
        super(PreviewWidget, self).__init__()
        self.resize(1000, 800)
        self.setWindowTitle('Frame Stamp Preview')
        self.setAcceptDrops(True)
        self.setMinimumHeight(self.padding*3)
        self.setMinimumWidth(self.padding*3)
        self.pixmap = None
        self.update_image()
        print self.pixmap

    def update_image(self, path=None):
        if path:
            self.pixmap = frame_stamp.add_stamp(frame_stamp.data_example, image_path=path, qtpixmap=1, bg_color=(0,0,0,150), backdrop=1)
        else:
            defimage = frame_stamp.default_image(w=800, h=600, checkersize=50)
            self.pixmap = frame_stamp.add_stamp(frame_stamp.data_example, raw_image=defimage, qtpixmap=1, bg_color=(0,0,0,150), backdrop=1)
        self.update()

    def paintEvent(self, event):
        p = QPainter()
        p.begin(self)
        # p.setRenderHint(QPainter.HighQualityAntialiasing, True)
        rec = self.visibleRegion().boundingRect()
        # bg
        p.setBrush(QBrush(QColor(*self.bg)))
        p.drawRect(rec)
        # pixmap
        if self.pixmap:
            scaleRect = self.pixmap.rect().intersected(rec.adjusted(self.padding, self.padding, -self.padding, -self.padding))
            if not scaleRect == self.pixmap.rect():
                pix = self.pixmap.scaled(scaleRect.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            else:
                pix = self.pixmap
            pixRec = pix.rect()
            pixRec.moveCenter(rec.center())
            p.drawPixmap(pixRec, pix)
        else:
            pass
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

if __name__ == '__main__':
    app = QApplication([])
    label = PreviewWidget()
    label.show()
    app.exec_()