from PySide.QtCore import *
from PySide.QtGui import *
import os, json, glob, shutil
from ..submitter_variables import join


col_width = 30

class RenderBocksClass(QTableWidget):
    layerRemovedSignal = Signal(str)
    def __init__(self, parent):
        super(RenderBocksClass, self).__init__(parent)
        # delete, layer, format, engine, output dir, camera and frames

        labels = ['X', 'Layer', 'DIR', 'Camera', 'F', 'E']
        self.setColumnCount(6)
        self.setHorizontalHeaderLabels(labels)
        header = self.horizontalHeader()
        self.path = None
        for c in 0,4,5:
            self.setColumnWidth(c, col_width)

        header.setResizeMode(1, QHeaderView.Stretch)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.itemDoubleClicked.connect(self.show_item_detail)


    def update_from_folder(self, path=None):
        self.setRowCount(0)
        if not path or not os.path.exists(path):
            return
        self.path = path
        datafiles = []
        for f in os.listdir(path):
            full = join(path,f)
            if os.path.isdir(full):
               jsns = glob.glob1(full, '*.json')
               if jsns:
                   datafiles.append(join(full,jsns[0]))
        if not datafiles:
            return
        map(self.add_row, datafiles)


    def add_row(self, datafile):
        try:
            data = json.load(open(datafile))
        except:
            return
        rows = self.rowCount()
        self.insertRow(rows)
        items = []

        it_remove = QPushButton('X')
        it_remove.clicked.connect(lambda x=datafile:self.remove_block(x))
        it_remove.setFixedSize(QSize(col_width-1,col_width-1))
        self.setCellWidget(rows,0, it_remove)
        # items.append(it_remove)

        it_layer = QTableWidgetItem(data['layer'])
        it_layer.setData(32, datafile)
        it_layer.setToolTip(data['layer'])
        self.setItem(rows,1, it_layer)
        items.append(it_layer)

        it_dir = QTableWidgetItem(data['outputdir'])
        it_dir.setTextAlignment(Qt.AlignCenter)
        it_dir.setToolTip(data['outputdir'])
        self.setItem(rows,2, it_dir)
        items.append(it_dir)

        if len(data['ranges']) == 1:
            cam = '%s (%s-%s)' % (data['ranges'][0]['camera'], data['ranges'][0]['start'], data['ranges'][0]['end'])
        else:
            cam = '%s cameras' % len(data['ranges'])
        it_cam = QTableWidgetItem(cam)
        it_cam.setTextAlignment(Qt.AlignCenter)
        self.setItem(rows,3, it_cam)
        items.append(it_cam)

        f = 'Mov' if data['ismove'] else 'Img'
        it_format = QTableWidgetItem(f)
        it_format.setTextAlignment(Qt.AlignCenter)
        self.setItem(rows,4, it_format)

        it_engine = QTableWidgetItem('AI' if data['engine'] == 'ai' else 'OGL')
        it_engine.setTextAlignment(Qt.AlignCenter)
        self.setItem(rows,5, it_engine)
        items.append(it_engine)
        #
        # it_id = QTableWidgetItem(data['id'])
        # it_id.setTextAlignment(Qt.AlignCenter)
        # self.setItem(rows,6, it_id)
        # items.append(it_id)

        for it in items:
            it.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

    def show_item_detail(self, it):
        row =  it.row()
        f = self.item(row, 1).data(32)
        import webbrowser
        webbrowser.open(os.path.dirname(f))
        print json.load(open(f))

    def get_data_files(self):
        datafiles = []
        for i in range(self.rowCount()):
            datafiles.append(self.item(i, 1).data(32))
        return datafiles

    def remove_block(self, path):
        path = os.path.dirname(path)
        if os.path.exists(path):
            shutil.rmtree(path)
        else:
            print 'Path already deleted', path
        self.update_from_folder(self.path)
