import os, sys, json, subprocess, re, time, imp
from PySide.QtCore import *
from PySide.QtGui import *

if os.getenv('PYTHONHOME'):
    del os.environ['PYTHONHOME']

class status():
    ERROR       = 'ERROR'       # print error and stop process
    PROGRESS    = 'PROGRESS'    # progress in percent (0-100)
    ACTIVITY    = 'ACTIVITY'    # display activity on task
    MESSAGE     = 'MESSAGE'     # just print message
    WARNING     = 'WARNING'     # selected message as warning!!!
    FRAME       = 'FRAME'       # switch to next frame
    PID         = 'PID'         # echo process PID

def printer(msg, stat=status.MESSAGE):
    print ('%s::%s' % (stat, msg))
    sys.stdout.flush()

if __file__ == sys.argv[-1]:
    printer('Data file not set', status.ERROR)
    sys.exit()
args = sys.argv[1:]
datafile = args[0]
if not os.path.exists(datafile):
    printer('Data file not exists', status.ERROR)
    sys.exit()
try:
    data = json.load(open(datafile))
except:
    printer('Data file can not be read', status.ERROR)
    sys.exit()

if len(args) > 1:
    rng = args[1]
else:
    rng = 0

# get engine
engine = data.get('engine')
if not engine:
    printer('Engine not set', status.ERROR)
    sys.exit()

# get maya dir
mayadir = data.get('mayadir')
if not mayadir:
    printer('Maya install dir not set', status.ERROR)
    sys.exit()

#######################
# DEFINE ENV !!!!!!!!!!
#######################

if not engine in ['hw', 'blast']:
    printer('Render engine not support', status.ERROR)
    sys.exit(1)
    pass


bin = '"%s"' % os.path.join(mayadir, 'bin', 'maya.exe').replace('/','\\')
# create cmd
# render_cmd = r'''{bin} -nosplash -command \"python(\\"import sys;sys.path.append('{pypath}');import render_maya_ui\\")\" {oglrender} {datafile} {rangenum}'''.format(
#     bin=bin,
#     pypath=os.path.dirname(__file__).replace('\\','/'),
#     oglrender=os.path.join(os.path.dirname(__file__),'render_ogl.py').replace('\\','/'),
#     datafile=datafile,
#     rangenum=rng
# )
render_args = [
    '-nosplash',
    '-command',
    '''python(\"import sys;sys.path.append('%s');import render_maya_ui\")''' % os.path.dirname(__file__).replace('\\','/'),
    os.path.join(os.path.dirname(__file__),'render_ogl.py').replace('\\','/'),
    datafile,
    rng
]
# print (render_cmd)

class AiRenderer(QObject):
    def __init__(self):
        super(AiRenderer, self).__init__()
        self.counter = os.path.join(data['tmpdir'], '.counter_%s' % rng)
        self.reset_counter()
        self.last = 0

    def start(self, cmd, args):
        printer('Maya Playblast', status.ACTIVITY)
        time.sleep(0.5)
        self.procesor = QProcess()
        self.procesor.finished.connect(self.finish)
        self.procesor.start(cmd, args)
        printer(str(self.procesor.pid()), status.PID)
        QTimer.singleShot(1000, self.check_env)

    def check_env(self):
        if os.path.exists(self.counter):
            prcnt = (json.load(open(self.counter)))
            if not prcnt == self.last:
                printer(prcnt, status.PROGRESS)
            self.last = prcnt
        QTimer.singleShot(2000, self.check_env)

    def reset_counter(self):
        if os.path.exists(self.counter):
            os.remove(self.counter)

    def finish(self):
        self.reset_counter()
        sys.exit()


app = QApplication([])
R = AiRenderer()
R.start(bin, render_args)
app.exec_()