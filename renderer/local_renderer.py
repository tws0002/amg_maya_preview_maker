from PySide.QtCore import *
from PySide.QtGui import *
import os, sys, argparse, json, re, shutil, datetime

parser = argparse.ArgumentParser(description='Render locally')
parser.add_argument('-d', '--datafile',
                    help='Input JSON data file')
parser.add_argument('-p', '--paused',
                    type=int,
                    help='Paused')
parser.add_argument('-c', '--commands',
                    help='Generate commands only')

pyth = '"%s"' % sys.executable

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


class ProcessMonitor(QMainWindow):
    def __init__(self, datafile, paused=False):
        super(ProcessMonitor, self).__init__()
        self.setWindowTitle('AMG Render Monitor')
        self.amg_icon()
        self.w = QWidget()
        self.setCentralWidget(self.w)
        self.ly = QVBoxLayout()
        self.w.setLayout(self.ly)
        self.start_btn = QPushButton('Start')
        self.start_btn.clicked.connect(self.start)
        self.ly.addWidget(self.start_btn)
        self.stop_btn = QPushButton('Stop')
        self.stop_btn.clicked.connect(self.stop_clicked)
        self.ly.addWidget(self.stop_btn)
        self.start_btn.setVisible(bool(paused))
        self.stop_btn.setVisible(not bool(paused))

        self.message_lb = QLabel('Waiting...')
        self.ly.addWidget(self.message_lb)
        self.activity_lb = QLabel('')
        self.ly.addWidget(self.activity_lb)
        self.progres_pb = QProgressBar()
        self.ly.addWidget(self.progres_pb)
        self.out_tb = QTextBrowser()
        self.ly.addWidget(self.out_tb)
        self.close_cbx = QCheckBox('Close on finish')
        self.close_cbx.setChecked(1)
        self.ly.addWidget(self.close_cbx)
        self.resize(650, 350)
        # vars
        self.df = datafile
        self.cmds = []
        self.command_count = 0
        self.process = QProcess()
        self.do_clean_files = False
        self.current_pid = None
        self.stopped = False
        # start
        self.out('Starting...')
        self.out('Data file: %s' % datafile)
        if not paused:
            self.start()
        else:
            self.out('PRESS START TO BEGIN RENDER')

    def out(self, *msg):
        self.out_tb.append(' '.join([str(x) for x in msg]))

    def start(self):
        datafiles = json.load(open(self.df)).get('datafiles')
        if not datafiles:
            self.out('Data files not found')
            return
        commands = []
        datafiles = [dict(path=x, data=json.load(open(x))) for x in datafiles]
        for data in datafiles:
            if data['data']['engine'] == 'ai':
                renderer = os.path.join(os.path.dirname(__file__), 'renderer_ai.py')
                cmd = ' '.join([pyth, renderer, ' ']).replace('/','\\')
                for i, rng in enumerate(data['data']['ranges']):
                    rcmd = cmd + '%s %s %s %s ' % (data['path'], i, rng['start'], rng['end'])
                    commands.append(dict(
                        cmd=rcmd,
                        message='Render AI frames:%s-%s' % (rng['start'], rng['end'])
                    ))

            elif data['data']['engine'] in ['blast', 'hw']:
                renderer = os.path.join(os.path.dirname(__file__), 'renderer_ogl.py')
                cmd = ' '.join([pyth, renderer, ' ']).replace('/','\\')
                for i, rng in enumerate(data['data']['ranges']):
                    rcmd = cmd + '%s %s' % (data['path'], i)
                    commands.append(dict(
                        cmd=rcmd,
                        message='Render OGL frames:%s-%s' % (rng['start'], rng['end'])
                    ))

            if data['data']['stamp']:
                renderer = os.path.join(os.path.dirname(__file__), 'render_stamp.py')
                cmd = ' '.join([pyth, renderer, data['path']]).replace('/','\\')
                commands.append(dict(
                        cmd=cmd,
                        message='Stamping'
                    ))
            if data['data']['ismove']:
                renderer = os.path.join(os.path.dirname(__file__), 'renderer_mp4.py')
                cmd = ' '.join([pyth, renderer, data['path']]).replace('/','\\')
                commands.append(dict(
                        cmd=cmd,
                        message='Images to MP4'
                    ))
        # post
        renderer = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'post_command.py')
        cmd = ' '.join([pyth, renderer, self.df]).replace('/','\\')
        commands.append(dict(
                        cmd=cmd,
                        message='Post Command'
                    ))
        # json.dump(commands, open('c:/commands.json', 'w'), indent=2)
        # os.startfile('c:/commands.json')
        self.out('Start render')
        self.start_btn.hide()
        self.stop_btn.show()
        if commands_only:
            json.dump(commands, open('c:/commands.json', 'w'), indent=2)
            os.startfile('d:/commands.json')
            sys.exit()
        else:
            self.execute_commands(commands)

    def execute_commands(self, cmds):
        self.cmds = cmds
        self.command_count = len(cmds)
        self.next_command()

    def next_command(self):
        if self.stopped == True:
            self.stop_btn.hide()
            # self.stop()
            return
        self.progres_pb.setValue(0)
        self.activity_lb.setText('')
        if self.cmds:
            cmd = self.cmds.pop(0)
            self.out('_'*50+'  '+datetime.datetime.now().strftime("%Y.%m.%d %H:%M:%S"))
            label = '%s (%s / %s)' % (cmd['message'],self.command_count- len(self.cmds), self.command_count)

            self.message_lb.setText(label)
            self.out(cmd['message'])
            # self.out(cmd['cmd'])
            if self.process:
                self.process.kill()
                self.process.waitForFinished()
            self.process = QProcess()
            self.process.setProcessChannelMode(QProcess.MergedChannels)
            self.process.finished.connect(self.next)
            # self.process.finished.connect(self.next_command)
            self.process.readyRead.connect(self.process_output)
            self.process.start(cmd['cmd'])
        else:
            self.stop_btn.setDisabled(1)
            self.stopped = True
            self.stop_clicked(force=False, message='Finished')

    def next(self, code):
        if code:
            self.out('ERROR RENDER')
            self.stop()
        if self.stopped:
            return
        if self.process.isOpen():
            self.process.terminate()
            self.process.waitForFinished()

        QTimer.singleShot(1000, self.next_command)


    def process_output(self):
        output = self.process.readAll()
        if not isinstance(output, str):
            output = str(output)
        output = str(output).strip()
        # print output
        if output:
            other = True
            act = re.match(status.ACTIVITY + '::(.+)', output.strip())
            if act:
                self.activity_lb.setText(act.group(1))
                other = False
                # return
            m = re.match(status.PROGRESS + '::(\d+)', output.strip())
            if m:
                prc = int(m.group(1))
                self.progres_pb.setValue(prc)
                other = False
                # return
            pid = re.findall(status.PID + '::(\d+)', output.strip())
            if pid:
                self.current_pid = int(pid[0])
                other = False
                # return
            img = re.findall('%s::([\d\w/\\:.\\-_]+)' % status.IMAGE, output.strip())
            if img:
                printer(img[0])
                self.out(img[0])
                other = False
                # return
            if other:
                # pass
                print output


############################################# STOP

    def closeEvent(self, event):
        if not self.process.isOpen():
            sys.exit()
        event.ignore()
        self.stop_clicked(force=True)

    def stop_clicked(self, force=False, message=None):
        if not force and not self.stopped:
            if not QMessageBox.question(self, 'Cancel render', 'Cancel the render and exit?', QMessageBox.Yes|QMessageBox.No, QMessageBox.No) == QMessageBox.Yes:
                return
        self.stop()
        if self.close_cbx.isChecked() or force:
            QTimer.singleShot(2000 if not force else 200, sys.exit)

    def stop(self, message=None):
        message = message or 'Stopped'
        self.stopped = True
        print 'Stop Render Process'
        self.stop_btn.setEnabled(0)
        self.out('Stop process...')
        if self.process:
            if self.current_pid:
                print 'Kill PID:', self.current_pid
                QProcess.execute('taskkill /PID %s /F' % self.current_pid)
                self.process.kill()
                self.process.terminate()
                self.process.waitForFinished()
                self.current_pid = None
        QTimer.singleShot(1000, self.clean_files)
        self.message_lb.setText(message)
        self.activity_lb.setText('')
        self.progres_pb.setValue(0)

    def clean_files(self):
        return
        path = os.path.dirname(self.df)
        try:
            if os.path.exists(path):
                shutil.rmtree(path)
                self.out('Remove', path)
                print 'Removed',path
        except:
            self.out('Error remove folder', path)
            print 'Error remove folder',path

    def amg_icon(self):
        text = 'AMG'
        fs = 15
        pix = QPixmap(48,48)
        pix.fill(QColor(0,0,0,0))
        pix.fill(QColor(55,55,55,255))
        f = QFont('Arial',fs)
        f.setBold(1)

        painter = QPainter()
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform | QPainter.HighQualityAntialiasing)
        painter.begin(pix)
        painter.setBrush(QColor(Qt.red))
        painter.setPen(QPen(QColor(254,127,0)))
        painter.setFont(f)
        painter.drawText(pix.rect(),  Qt.AlignCenter,text)
        painter.end()

        self.setWindowIcon(QIcon(pix))

def exit():
    raw_input('Press Enter to exit...')
    sys.exit(1)

if __name__ == '__main__':
    args = parser.parse_args()
    if not args.datafile:
        print 'No data files defined'
        exit()
    err = False

    try:
        json.load(open(args.datafile))
    except:
        print 'Error read data file %s' % args.datafile
        exit()
    if err:
        exit()
    commands_only = bool(args.commands)
    app = QApplication([])
    w = ProcessMonitor(args.datafile, args.paused)
    w.show()
    app.exec_()