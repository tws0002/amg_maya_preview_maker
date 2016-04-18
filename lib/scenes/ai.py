from pymel.core import *

try:
    if not pluginInfo('mtoa.mll', q=1, l=1):
        loadPlugin('mtoa.mll')
except:
    print 'Error load Arnold Renderer'

# set renderer
evalDeferred("mel.eval('setCurrentRenderer(\"arnold\")' )")

mel.setCurrentRenderer("arnold")

# set attributes
ar = PyNode('defaultArnoldRenderOptions')
# samples
ar.AASamples.set(5)
ar.GIRefractionSamples.set(1)
ar.GIGlossySamples.set(1)
ar.GIDiffuseSamples.set(1)
ar.GISssSamples.set(2)
ar.GIVolumeSamples.set(0)

# setAttr "hardwareRenderingGlobals.transparencyAlgorithm" 3;
# setAttr "hardwareRenderingGlobals.transparencyQuality" 0.279202;

# setup viewport lighting
for mp in getPanel(type=ui.Panel('modelPanel')):
    modelEditor(mp, edit=1, dl="default", shadows=0, dtx=1, lights=1)