import sys, os, json, imp, time, random, math, shutil
from PySide.QtCore import *
from PySide.QtGui import *
from pymel.core import *
import maya.OpenMayaUI as omui
from shiboken import wrapInstance as wrp
def getMayaWindow():
    ptr = omui.MQtUtil.mainWindow()
    if ptr is not None:
        return wrp(long(ptr), QMainWindow)
qMaya = getMayaWindow()

msg_env = 'MAYA_PROGRESS_MSG'

def fit(value, start, end):
    old_value = float(value)
    old_min = float(start)
    old_max = float(end)
    new_min = 0.0
    new_max = 100.0
    return int(math.floor(( (old_value - old_min) / (old_max - old_min) ) * (new_max - new_min) + new_min))


# qMaya.hide()
qMaya.setWindowState(Qt.WindowMinimized)



ogl_renderer, dataflie, rng = sys.argv[-3:]
data = json.load(open(dataflie))
rng = int(rng)
if data['viewport_backdrop']:
    displayPref(displayGradient=0)
    displayRGBColor('background', *data['viewport_backdrop'])
    # ogl_black_background(True,data['viewport_backdrop'] )
else:
    displayPref(displayGradient=1)


ogl = imp.load_source('ogl', ogl_renderer)
current_range = data['ranges'][rng]

outdir = os.path.join(data['tmpdir'], '_'.join([ 'render_range', str(current_range['start']), str(current_range['end']) ])).replace('/','\\')
if not os.path.exists(outdir):
    os.makedirs(outdir)

# load scene
openFile(data['mayascene'],prompt=False)
# get layer
nt.RenderLayer(data['layer']).setCurrent()
# ogl  data
ogl_data = data.get('ogl_data')
if ogl_data:
    if 'ao_enable' in ogl_data:
        PyNode('hardwareRenderingGlobals').ssaoEnable.set(ogl_data['ao_enable'])

# render
counter = os.path.join(data['tmpdir'], '.counter_%s' % rng)

if data['engine'] == 'hw':
    hw = PyNode('hardwareRenderingGlobals')
    hw.renderMode.set(2)
    rg = PyNode('defaultRenderGlobals')
    rg.imageFormat.set(8)
    rg.animation.set(1)
    rg.outFormatControl.set(0)
    rg.extensionPadding.set(4)
    rg.putFrameBeforeExt.set(1)

    name = data['outfilename']
    mel.setProject(outdir)
    hw = PyNode('hardwareRenderingGlobals')
    hw.multiSampleEnable.set(1)
    hw.multiSampleCount.set(16)
    hw.renderMode.set(2)
    rg = PyNode('defaultRenderGlobals')
    old_format = rg.imageFormat.get()
    old_imagePrefix = rg.imageFilePrefix.get()
    rg.imageFormat.set(8)
    files = []
    pad = max([4, len(str(current_range['end']))])

    frame_outfile = name + '_'
    rg.imageFilePrefix.set(frame_outfile)
    for frame in range(current_range['start'], current_range['end']+1):
        prcnt = fit(frame, current_range['start'], current_range['end'])
        json.dump(prcnt, open(counter, 'w'))
        name, ext = data['outfilename'], '.jpg'
        # frame_outfile = name + '_' + str(frame).zfill(pad) + ext
        # rg.imageFilePrefix.set(frame_outfile)
        setCurrentTime(frame)
        outfile = ogsRender(activeRenderTargetFormat='R16G16B16A16_FLOAT', camera=current_range['camera'],
                            width=data["resolution"][0], height=data["resolution"][1] )
        files.append(outfile)
    for file in files:
        old = file.replace('\\','/')
        m = re.match(r'(\w+_)(\.)(\d+\.\w{2,4}$)', os.path.basename(file))
        if m:
            newname = m.group(1)+m.group(3)
        else:
            newname = os.path.basename(file)
        new = os.path.join(outdir, newname).replace('\\','/')
        if os.path.exists(new):
            os.remove(new)
        shutil.move(old, new)
    for f in os.listdir(outdir):
        full = os.path.join(outdir, f)
        if os.path.isdir(full):
            shutil.rmtree(full)
        elif os.path.isfile(full):
            if os.path.splitext(f)[-1] == '.mel':
                os.remove(full)

else:
    outfile = os.path.join(outdir, data['outfilename'] + '.jpg')
    name, ext = os.path.splitext(outfile)

    for frame in range(current_range['start'], current_range['end']+1):
        frame_outfile = name + '_' + str(frame).zfill(max([4, len(str(current_range['end']))])) + ext
        prcnt = fit(frame, current_range['start'], current_range['end'])
        json.dump(prcnt, open(counter, 'w'))
        ogl.render_frame_ogl(data["resolution"], frame_outfile, frame,  current_range['camera'], engine=data['engine'] )

# exit

if not outdir in data['jpgfiles']:
    data['jpgfiles'].append(outdir)
    json.dump(data, open(dataflie, 'w'), indent=4)

QTimer.singleShot(3000, lambda :mel.quit(force=1))