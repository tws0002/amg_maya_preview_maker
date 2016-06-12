from PySide.QtCore import *

import os, sys, json, re, time

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

def incName(name):
    nm, ext = os.path.splitext(name)
    digit = re.search(r'(.*)(\d+)$', nm)
    if digit:
        next = digit.group(1) + str(int(digit.group(2)) + 1)
    else:
        next = nm + '1'
    return next + ext
app_ffmpeg = None

conf = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json').replace('\\','/')
if os.path.exists(conf):
    conf_data = json.load(open(conf))
    app_ffmpeg = conf_data.get('ffmpeg_path')
if not app_ffmpeg:
    self_ffmpeg = os.path.join(os.path.dirname(os.path.dirname(__file__)),'tools/bin/ffmpeg.exe')
    print self_ffmpeg
    if os.path.exists(self_ffmpeg):
        app_ffmpeg = self_ffmpeg

if not app_ffmpeg:
    printer('FFMPEG not found', status.ERROR)
    sys.exit(1)



class FFMPEGRenderer(QObject):
    def __init__(self, datafile, outdir, frame_count):
        super(FFMPEGRenderer, self).__init__()
    def start(self, cmd):
        self.procesor = Executor(frame_count)
        self.procesor.finishSignal.connect(self.finish)
        self.procesor.start(cmd)
        self.datafile = datafile
        self.outdir = outfile


    def finish(self):
        data = json.load(open(self.datafile))
        data['outfiles'].append(self.outdir)
        json.dump(data, open(self.datafile, 'w'), indent=2)
        sys.exit()

error_lines = ['Unable to find', 'Invalid argument', 'Could find no file']

class Executor(QObject):
    finishSignal = Signal()
    def __init__(self, frame_count):
        super(Executor, self).__init__()
        self.process = None
        self.frame_count = frame_count

    def start(self, cmd):
        printer('Rendering MP4', status.ACTIVITY)
        time.sleep(0.5)
        print '>'*10,cmd
        # printer('Execute command: %s' % cmd, status.MESSAGE)
        self.process = QProcess()
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.finished.connect(self.finish)
        self.process.readyRead.connect(self.process_output)
        self.process.start(cmd)
        printer(str(self.process.pid()), status.PID)

    def process_output(self):
        output = self.process.readAll()
        if not isinstance(output, str):
            output = str(output)
        output = str(output).strip()
        if output:
            f = re.search(r'frame=\s*(\d+)', output)
            # print output
            if f:
                num = f.group(1)
                out = int((100.0/self.frame_count)*float(num))
                printer(out, status.PROGRESS)
            for error in error_lines:
                f = re.findall(error, output)
                if f:
                    printer(output, status.ERROR)
                    sys.exit()


    def finish(self, *args):
        self.deleteLater()
        self.finishSignal.emit()


if __name__ == '__main__':
    datafile = sys.argv[-1]
    data = json.load(open(datafile))
    if not data.get('jpgfiles'):
        printer('Not image sequences in data file', status.ERROR)
    if len(data['jpgfiles']) > 1:
        # source_folder = ''
        #todo: work work several ranges
        source_folder = data['jpgfiles'][0]
        sys.exit()
    else:
        source_folder = data['jpgfiles'][0]
    # printer('Convert images to MP4', status.ACTIVITY)
    num = 1
    filename = None
    frame_count = len(os.listdir(source_folder))
    for f in os.listdir(source_folder):
        m = re.match(r'\w+(\.|_)(\d+).\w+', f)
        if m:
            num = max([len(m.group(2)), num])
            filename = m.group(0).replace(m.group(2), '%%%sd' % num)

    if not filename:
        sys.exit()
    filename = os.path.normpath(os.path.join(source_folder, filename))
    if not os.path.exists(data['outputdir']):
        os.makedirs(data['outputdir'])
    outfile = os.path.join(data['tmpdir'], data['outfilename'] + '.mp4').replace('\\','/')
    while os.path.exists(outfile):
        outfile = incName(outfile)
    printer('OUT FILE ' + outfile)

    cmd = r'{ffmpeg} -y -r 24 -f image2 -s {width}x{height} -i {input} -vcodec libx264 -crf 25  {outdir}'.format(
        ffmpeg=app_ffmpeg,
        width=data["resolution"][0],
        height=data["resolution"][1],
        input=filename,
        outdir=outfile
    )
    app = QCoreApplication([])
    r = FFMPEGRenderer(datafile, outfile.replace('\\','/'), frame_count)
    printer(cmd)
    r.start(cmd)

    app.exec_()
    # os.system(cmd)
