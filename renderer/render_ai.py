from pymel.core import *
import tempfile, random
import arnold as ai
from ..submitter_variables import join
# import submitter_variables as v

def export_temp_frame(resolution, cam):
        d = tempfile.gettempdir()
        id = random.randrange(10000, 99999)
        fi = join(d,'preview_image_%s' % id)
        fa = fi + '.ass'

        rg = PyNode('defaultRenderGlobals')
        dr = PyNode('defaultResolution')
        ar = PyNode('defaultArnoldDriver')

        # backup
        old_format = ar.aiTranslator.get()
        oldW, oldH =dr.width.get(), dr.height.get()
        old_path = rg.imageFilePrefix.get() or ''
        old_gamma = ar.gamma.get()
        anim_pref = [rg.outFormatControl.get(),rg.animation.get(), rg.putFrameBeforeExt.get(), rg.extensionPadding.get()]
        dr.width.set(resolution[0])
        dr.height.set(resolution[1])
        ar.gamma.set(2.2**2)
        rg.outFormatControl.set(0)
        rg.animation.set(1)
        rg.putFrameBeforeExt.set(1)
        rg.extensionPadding.get(len(str(int(max(env.getPlaybackTimes())))))
        # set values
        ar.aiTranslator.set('jpeg')
        rg.imageFilePrefix.set(fi)
        # render ass
        file = cmds.arnoldExportAss(f=fa, startFrame=currentTime(), endFrame=currentTime(),
                                 mask=255, lightLinks=1, frameStep=1.0, shadowLinks=1,
                                 cam=PyNode(cam).getShape().longName())
        # restore
        ar.aiTranslator.set(old_format, type='string')
        rg.imageFilePrefix.set(old_path, type='string')
        dr.width.set(oldW)
        dr.height.set(oldH)
        ar.gamma.set(2.2)
        rg.outFormatControl.set(anim_pref[0])
        rg.animation.set(anim_pref[1])
        rg.putFrameBeforeExt.set(anim_pref[2])
        rg.extensionPadding.get(anim_pref[3])
        return file[0]

def render_ass(ass, remove_ass=False):
    imagefilename = None
    ai.AiBegin()
    ai.AiLoadPlugins(os.environ['ARNOLD_PLUGIN_PATH'])
    ai.AiASSLoad (ass, ai.AI_NODE_ALL)
    ai.AiRender()
    ai.AiEnd()
    # read out file
    ai.AiBegin()
    ai.AiMsgSetConsoleFlags(ai.AI_LOG_ALL)
    ai.AiASSLoad(ass, ai.AI_NODE_ALL)
    iter = ai.AiUniverseGetNodeIterator(ai.AI_NODE_ALL)
    while not ai.AiNodeIteratorFinished(iter):
        node = ai.AiNodeIteratorGetNext(iter)
        if ai.AiNodeIs( node, "driver_jpeg" ):
            imagefilename = ai.AiNodeGetStr( node, "filename" )
    ai.AiNodeIteratorDestroy(iter)
    ai.AiEnd()
    if remove_ass:
        os.remove(ass)
    return imagefilename
