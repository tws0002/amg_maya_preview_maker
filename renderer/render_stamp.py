from PySide.QtCore import *
from PySide.QtGui import *
import sys, json, imp, os, re, glob, math, copy, time

class status():
    ERROR       = 'ERROR'       # print error and stop process
    PROGRESS    = 'PROGRESS'    # progress in percent (0-100)
    ACTIVITY    = 'ACTIVITY'    # display activity on task
    MESSAGE     = 'MESSAGE'     # just print message
    WARNING     = 'WARNING'     # selected message as warning!!!
    FRAME       = 'FRAME'       # switch to next frame
    PID         = 'PID'         # echo process PID

datafile = sys.argv[-1]
# datafile = 'C:/amg_temp/afrender_439759/car.mb_afrender_submitter_layer_original_22552.json'
data = json.load(open(datafile))

stamper = imp.load_source('stamp', os.path.join(os.path.dirname(__file__), 'frame_stamp.py' ))

def printer(msg, stat=status.MESSAGE):
    print ('%s::%s' % (stat, msg))
    sys.stdout.flush()

def fit(value, start, end):
    old_value = float(value)
    old_min = float(start)
    old_max = float(end)
    new_min = 0.0
    new_max = 100.0
    return int(math.floor(( (old_value - old_min) / (old_max - old_min) ) * (new_max - new_min) + new_min))


def main():
    """
    input file
    output file
    data_file.json
    """
    if not sys.argv[1:]:
        print ('Arguments not set')
        exit()
    datafile = sys.argv[-1]
    data = json.load(open(datafile))
    printer('Stamping frames', status.ACTIVITY)
    time.sleep(0.5)
    for folder in data['jpgfiles']:
        if os.path.isdir(folder):
            files = glob.glob1(folder, '*.jpg')+glob.glob1(folder, '*.jpeg')
            for i, image in enumerate(files):

                cleandata = copy.deepcopy(data)
                image = os.path.join(folder,image).replace('\\','/')
                f = re.findall(r"(\d+)\.\w+$", os.path.basename(image))
                if f:
                    frame = int(f[0])
                else:
                    frame = i
                stamp = stamper.set_frame_number(cleandata['stamp']['stamp'], frame) or cleandata['stamp']['stamp']
                stamper.add_stamp(stamp,
                                  image,
                                  font_size=data['stamp'].get('font_size', stamper.default_font_size),
                                  bg_color=data['stamp'].get('bg_color', stamper.default_bg_color),
                                  logo=data.get('logo', True),
                                  font=data.get('font'),
                                  backdrop=data.get('backdrop')
                                  )
                prcnt = fit(i, 0, len(files))
                printer(prcnt, status.PROGRESS)
    sys.exit()

if __name__ == '__main__':
    if not QCoreApplication.instance():
        import PySide
        pyside_root = os.path.dirname(PySide.__file__)
        path = os.path.join(pyside_root, 'plugins').replace('\\','/')
        app = QApplication([])
        app.addLibraryPath(path)
        main()
        # app.exec_()
    else:
        main()
