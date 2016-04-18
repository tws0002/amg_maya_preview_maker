import os, json, sys, time, re
from PySide.QtCore import *
from PySide.QtGui import *

del os.environ['PYTHONHOME']

class status():
    ERROR       = 'ERROR'       # print error and stop process
    PROGRESS    = 'PROGRESS'    # progress in percent (0-100)
    ACTIVITY    = 'ACTIVITY'    # display activity on task
    MESSAGE     = 'MESSAGE'     # just print message
    WARNING     = 'WARNING'     # selected message as warning!!!
    FRAME       = 'FRAME'       # switch to next frame
    PID         = 'PID'         # echo process PID
    IMAGE       = 'IMAGE'       # saved image

def printer(msg, stat=status.MESSAGE):
    print ('%s::%s' % (stat, msg))
    sys.stdout.flush()

datafile, rng, start, end = sys.argv[-4:]

data = json.load(open(datafile))
current_range = data['ranges'][int(rng)]
renderer = os.path.join(os.path.normpath(data['mayadir']), 'bin','Render.exe')

mtoa_path = data.get('mtoa_path')
if mtoa_path:
    sys.path.append(os.path.join(mtoa_path, 'scripts'))

# if current_range['orto']:
#     wh = data["resolution_orto"]
# else:
#     wh = data["resolution_persp"]

outdir = os.path.join(data['tmpdir'], '_'.join([ 'render_range', str(current_range['start']), str(current_range['end']) ])).replace('/','\\')
if not os.path.exists(outdir):
    os.makedirs(outdir)

render_cmd = '{render} -s {start} -e {end} -b {step} -r arnold -cam {cam} -rt 0 -im {imagename} -x {width} -y {height}  -rl {layer} -rd {outdir} -ai:lve 2 -ai:ltc 1 {scene}'.format(
    render = renderer,
    start = start,
    end=end,
    step=current_range['step'],
    cam=current_range['camera'],
    width=data["resolution"][0],
    height=data["resolution"][1],
    layer=data['layer'],
    outdir=outdir,
    imagename=data['outfilename'],
    scene=data['mayascene'].replace('/','\\')
)
# print (cmd)
# os.system(cmd)

class AiRenderer(QObject):
    def __init__(self):
        super(AiRenderer, self).__init__()
    def start(self, cmd):
        self.procesor = Executor()
        self.procesor.finishSignal.connect(sys.exit)
        # printer('AI COMMAND| %s' % cmd)
        self.procesor.start(cmd)


error_lines = ['Please check the scene name',]

class Executor(QObject):
    finishSignal = Signal()
    def __init__(self):
        super(Executor, self).__init__()
        self.process = None
        self.range = [0,0]
        self.current_frame = 0
        self.files = []

    def start(self, cmd):
        self.get_range(cmd)
        printer('Render frame %s' % (self.current_frame), status.ACTIVITY)
        time.sleep(0.5)
        # QTimer.singleShot(1000,lambda :printer('Execute command: %s' % cmd))
        self.process = QProcess()
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.finished.connect(self.finish)
        self.process.readyRead.connect(self.process_output)
        self.process.start(cmd)
        printer(str(self.process.pid()), status.PID)

    def get_range(self, cmd):
        start = int((re.findall(r"-s\s(\d+)",cmd) or [1])[0])
        end = int((re.findall(r"-e\s(\d+)",cmd) or [1])[0])
        self.range = [start, end]
        self.current_frame = start

    def process_output(self):
        output = self.process.readAll()
        if not isinstance(output, str):
            output = str(output)
        output = str(output).strip()
        if output:
            f = re.search(r'(\d+)% done', output)
            if f:
                num = f.group(1)
                out = int(float(num))
                printer(out, status.PROGRESS)
            fram = re.search(r'render done', output)
            if fram:
                self.current_frame += 1
                QTimer.singleShot(200,lambda :printer('Render frame %s' % self.current_frame, status.ACTIVITY))
            fil = re.search(r"writing file[\s`']+([\d\w/\\:.\\-_]+)", output)
            if fil:
                outfile = fil.group(1)
                self.files.append(outfile)
                printer(outfile, status.IMAGE)
            for error in error_lines:
                f = re.findall(error, output)
                if f:
                    printer(output, status.ERROR)
                    sys.exit()

    def finish(self, *args):
        dirs = [os.path.dirname(x) for x in self.files]
        d = json.load(open(datafile))
        d['jpgfiles'] = list(set(d['jpgfiles']+dirs))
        json.dump(d, open(datafile, 'w'), indent=2)
        self.deleteLater()
        self.finishSignal.emit()


app = QApplication([])
R = AiRenderer()
R.start(render_cmd)
app.exec_()