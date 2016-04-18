from PySide.QtCore import *
from PySide.QtGui import *
from pymel.core import util
import frame_stamp_options_UIs
reload(frame_stamp_options_UIs)
from ..renderer import frame_stamp
reload(frame_stamp)


class FrameStampOptions(QWidget, frame_stamp_options_UIs.Ui_Stamp_Options):
    dataChangedSignal = Signal()
    def __init__(self,  parent=None):
        super(FrameStampOptions, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.Tool)
        self.font_path_le.setText(frame_stamp.get_font(filepath=True))
        self.opacity_lb.setText(str(self.opacity_sld.value()))

        self.opacity_sld.valueChanged.connect(self.data_changed)
        self.font_path_le.editingFinished.connect(self.data_changed)
        self.font_size_sbx.valueChanged.connect(self.data_changed)
        self.backdrop_cbx.clicked.connect(self.data_changed)
        self.font_path_le.hide()
        self.label_4.hide()
        self.set_font_path_le.hide()

    def set_data(self, data):
        self.font_path_le.setText(data['font'])
        self.font_size_sbx.setValue(data['font_size'])
        self.opacity_sld.setValue(data['bg_color'][-1])
        self.backdrop_cbx.setChecked(data['backdrop'])

    def data_changed(self, *args):
        self.dataChangedSignal.emit()

    def get_data(self):
        data = dict(
            font=self.font_path_le.text(),
            font_size=self.font_size_sbx.value(),
            bg_color=[0,0,0, util.setRange(self.opacity_sld.value(), 0, 100, 0, 255)],
            backdrop=self.backdrop_cbx.isChecked())
        return data

