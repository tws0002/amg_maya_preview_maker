from pymel.core import *

# set renderer
# mel.eval('setCurrentRenderer("mayaHardware2")' )
mel.ActivateViewport20()
# setup renderer
hw = PyNode('hardwareRenderingGlobals')
rg = PyNode('defaultRenderGlobals')
# AO
hw.ssaoEnable.set(1)
hw.ssaoRadius.set(45)
hw.ssaoFilterRadius.set(32)
# AA
hw.lineAAEnable.set(1)
hw.multiSampleEnable.set(1)
hw.multiSampleCount.set(16)
# wire
hw.renderMode.set(2)
# setup viewport lighting
if [x for x in ls(lights=1) if not x.getParent().hasAttr('specialRigAttr')]:
    dl = 'all'
else:
    dl = 'default'
for mp in getPanel(type=ui.Panel('modelPanel')):
    modelEditor(mp, edit=1, dl=dl, shadows=1, dtx=1, udm=0, cameras=0, grid=0, lights=0, wireframeOnShaded=0)
# enable wireframe


# render
    # set image format to PNG ( TIFF 16 bit )
# rg.imageFormat.set(32)
    # set output path
# rg.imageFilePrefix.set('path')
    # render
# res = ogsRender(activeRenderTargetFormat='R16G16B16A16_FLOAT', layer='layername')
    # apply gamma
# C:\cg\maya\Maya2014\bin\imconvert.exe -gamma 2.2 source.png targer.png
