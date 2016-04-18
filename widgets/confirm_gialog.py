from __future__ import unicode_literals
from PySide.QtCore import *
from PySide.QtGui import *
import confirm_dialog_UIs
import os

class ConfirmDialog(QDialog, confirm_dialog_UIs.Ui_confirm):
    def __init__(self, data=None, parent=None):
        super(ConfirmDialog, self).__init__(parent)
        # self.setWindowFlags(Qt.Tool)
        self.setupUi(self)
        html = os.path.join(os.path.dirname(os.path.dirname(__file__)),'lib','submit_preview.html')
        if not os.path.exists(html):
            raise Exception('HTML source not found')
        self.html = open(html).read()
        # self.basedir = os.path.dirname(__file__)
        # self.view.setHtml('<h1 id="navbar">Prepare</h1>')
        self.view.setHtml(self.html)
        self.view.linkClicked.connect(self.link_clicked)
        self.continue_btn.clicked.connect(self.accept)
        if data:
            QTimer.singleShot(500, lambda : self.build_html(data))

    def build_html(self, data):
        for key, value in data.items():
            if isinstance(value, (str, unicode)):
                # if os.path.exists(value):
                    # self.basedir = QUrl(os.path.dirname(value))
                    # value = os.path.basename(value)
                self.html = self.html.replace(key, value)
            elif isinstance(value, (list, tuple)):
                elems = ['<li>%s</li>' % x for x in value]
                self.html = self.html.replace(key, '\n'.join(elems))
        self.html = self.html.replace('id="defaultblock" style="display: block"', 'id="defaultblock" style="display: none"').replace('id="tableblock" style="display: none"', 'id="tableblock" style="display: block"')
        self.show_html()

    def show_html(self):
        self.view.setHtml(self.html)

    def link_clicked(self, url):
        print url



data = {
    '$PREVIEW$':'D:/PW_DATA/WinFolders/desktop/previrew.png',
    '$CAMS$':['cam1', 'cam2', 'cam3'],
    '$LAYERS$':['layer1', 'layer2', 'layer3'],
    '$ENGINE$':'OpenGL',
    '$MAYAVER$':'2016',
    '$OUTDIR$':'c:/outdir',
    '$TMPDIR$':'x:/tmpdir',
    '$AFANASY$':['Use: YES', 'Server: i7'],
    '$OUTFILESINFO$':['Output file: MP4', 'Join videos: YES', 'Resolution: 1280x720'],
    '$SHOTGUN$':['Files to publish: 1','Comment: NoComment', 'Publish path: projects/dev/sequences/001/001/maya/review']
}


if __name__ == '__main__':
    app = QApplication([])
    w = ConfirmDialog()
    w.build_html(data)
    w.show()
    w.show_html()
    app.exec_()
