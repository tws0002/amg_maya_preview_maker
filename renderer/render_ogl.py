from pymel.core import *

def render_current_frame_ogl(resolution, outfile, engine='blast', cam=None ):
    """
    inside maya only
    """
    # layer = nt.RenderLayer.currentLayer()
    # print 'ENGINE', engine
    if engine == 'blast':
        rg = PyNode('defaultRenderGlobals')
        cam = cam or ui.PyUI(playblast(activeEditor=True)).getCamera()
        overscan = cam.overscan.get()
        displRes = cam.displayResolution.get()
        old_format = rg.imageFormat.get()
        rg.imageFormat.set(8)
        cam.overscan.set(1.0)
        cam.displayResolution.set(False)
        select(cl=1)
        lookThru(cam)
        # print 'RENDER TO', outfile
        playblast(
               frame=currentTime(),
               format="image",
               offScreen=0,
               viewer=False,
               completeFilename=outfile,
               widthHeight=[resolution[0], resolution[1]],
               showOrnaments=0,
               percent=100,
               quality=100)
        rg.imageFormat.set(old_format)
        cam.overscan.set(overscan)
        cam.displayResolution.set(displRes)
        return outfile
    elif engine == 'hw':
        outfile = os.path.splitext(outfile)[0]+'_<RenderLayer>'
        hw = PyNode('hardwareRenderingGlobals')
        hw.multiSampleEnable.set(1)
        hw.multiSampleCount.set(16)
        hw.renderMode.set(2)
        rg = PyNode('defaultRenderGlobals')
        old_format = rg.imageFormat.get()
        old_imagePrefix = rg.imageFilePrefix.get()
        rg.imageFormat.set(8)
        rg.imageFilePrefix.set(outfile)
        cam = ui.PyUI(playblast(activeEditor=True)).getCamera()
        outfile = ogsRender(activeRenderTargetFormat='R16G16B16A16_FLOAT', camera=cam, width=resolution[0], height=resolution[1] )
        rg.imageFormat.set(old_format)
        rg.imageFilePrefix.set(old_imagePrefix or '')
        return outfile

def render_frame_ogl(resolution, outfile, frame, camera,  engine='blast' ):
    """
    inside maya only
    """
    # layer = nt.RenderLayer.currentLayer()
    if engine == 'blast':
        rg = PyNode('defaultRenderGlobals')
        cam = PyNode(camera)
        overscan = cam.overscan.get()
        displRes = cam.displayResolution.get()
        old_format = rg.imageFormat.get()
        rg.imageFormat.set(8)
        cam.overscan.set(1.0)
        cam.displayResolution.set(False)
        lookThru(cam)
        select(cl=1)
        playblast(
               frame=frame,
               format="image",
               offScreen=0,
               viewer=False,
               completeFilename=outfile,
               widthHeight=[resolution[0], resolution[1]],
               showOrnaments=0,
               percent=100,
               quality=100)
        rg.imageFormat.set(old_format)
        cam.overscan.set(overscan)
        cam.displayResolution.set(displRes)
        return outfile
    elif engine == 'hw':
        hw = PyNode('hardwareRenderingGlobals')
        hw.multiSampleEnable.set(1)
        hw.multiSampleCount.set(16)
        hw.renderMode.set(2)
        rg = PyNode('defaultRenderGlobals')
        old_format = rg.imageFormat.get()
        old_imagePrefix = rg.imageFilePrefix.get()
        rg.imageFormat.set(8)
        rg.imageFilePrefix.set(outfile)
        cam = ui.PyUI(playblast(activeEditor=True)).getCamera()
        outfile = ogsRender(activeRenderTargetFormat='R16G16B16A16_FLOAT', enableMultisample=1, camera=cam, width=resolution[0], height=resolution[1] )
        rg.imageFormat.set(old_format)
        rg.imageFilePrefix.set(old_imagePrefix or '')
        return outfile

def render_framerange_ogl(resolution, outfile, framerange, engine='blast', camera=None):
    """
    inside maya only
    """
    # layer = nt.RenderLayer.currentLayer()
    cam = camera or ui.PyUI(playblast(activeEditor=True)).getCamera()
    files = []

    if engine == 'blast':
        rg = PyNode('defaultRenderGlobals')
        overscan = cam.overscan.get()
        displRes = cam.displayResolution.get()
        old_format = rg.imageFormat.get()
        rg.imageFormat.set(8)
        cam.overscan.set(1.0)
        cam.displayResolution.set(False)
        select(cl=1)
        for frame in range(framerange[0],framerange[1]+1):
            name, ext = os.path.splitext(outfile)
            frame_outfile = name + '_' + str(frame).zfill(max([4, len(framerange)])) + ext
            playblast(
                   frame=frame,
                   format="image",
                   offScreen=True,
                   viewer=False,
                   completeFilename=frame_outfile,
                   widthHeight=[resolution[0], resolution[1]],
                   showOrnaments=0,
                   percent=100,
                   quality=100)
            files.append(frame_outfile)
        rg.imageFormat.set(old_format)
        cam.overscan.set(overscan)
        cam.displayResolution.set(displRes)
        return files
    elif engine == 'hw':
        hw = PyNode('hardwareRenderingGlobals')
        hw.multiSampleEnable.set(1)
        hw.multiSampleCount.set(16)
        hw.renderMode.set(2)
        rg = PyNode('defaultRenderGlobals')
        old_format = rg.imageFormat.get()
        old_imagePrefix = rg.imageFilePrefix.get()
        rg.imageFormat.set(8)
        rg.putFrameBeforeExt.set(1)
        for frame in range(framerange[0],framerange[1]+1):
            name, ext = os.path.splitext(outfile)
            frame_outfile = name + '_' + str(frame).zfill(max([4, len(framerange)])) + ext
            rg.imageFilePrefix.set(frame_outfile)
            setCurrentTime(frame)
            outfile = ogsRender(activeRenderTargetFormat='R16G16B16A16_FLOAT', camera=cam, width=resolution[0], height=resolution[1] )
            files.append(frame_outfile)
        rg.imageFormat.set(old_format)
        if old_imagePrefix:
            rg.imageFilePrefix.set(old_imagePrefix)
        return files