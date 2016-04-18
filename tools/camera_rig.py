from PySide.QtCore import *
from PySide.QtGui import *
import json, math
from pymel.core import *
from .. import submitter_variables as v
reload(v)

import object_set
reload(object_set)

def boundBox(bb):
    undoInfo(openChunk=1)
    box, sh = polyCube()
    delete(box, ch=1)
    move(box.vtx[0], bb.min()[0],bb.min()[1],bb.max()[2], os=1, wd=1)
    move(box.vtx[1], bb.max()[0],bb.min()[1],bb.max()[2], os=1, wd=1)
    move(box.vtx[2], bb.min()[0],bb.max()[1],bb.max()[2], os=1, wd=1)
    move(box.vtx[3], bb.max()[0],bb.max()[1],bb.max()[2], os=1, wd=1)
    move(box.vtx[4], bb.min()[0],bb.max()[1],bb.min()[2], os=1, wd=1)
    move(box.vtx[5], bb.max()[0],bb.max()[1],bb.min()[2], os=1, wd=1)
    move(box.vtx[6], bb.min()[0],bb.min()[1],bb.min()[2], os=1, wd=1)
    move(box.vtx[7], bb.max()[0],bb.min()[1],bb.min()[2], os=1, wd=1)
    undoInfo(closeChunk=1)
    return box

class BaseRig(object):
    title = 'Base'
    groupName = 'camera_rig'
    camera_name = 'camera_rig'
    rig_attr_name = 'submitterCameraRig'
    cam_attr_name = 'submitterOptions'
    def __init__(self):
        super(BaseRig, self).__init__()

    def create_root_group(self):
        setup_group = createNode('transform', name=self.groupName)
        addAttr(setup_group, ln=self.rig_attr_name+'_root', dt='string')
        setup_group.attr(self.rig_attr_name+'_root').set(self.title +' camera rig root')
        return setup_group

    @classmethod
    def get_bounding_box(cls, obj=None):
        if obj is None:
            obj = object_set.content()
        if not obj:
            return
        if isinstance(obj, list):
            bboxes = []
            for o in obj:
                try:
                    bboxes.append(o.getBoundingBox(space='world'))
                except:
                    pass
            bb = cls.bb_sum(*bboxes)
        else:
            bb = obj.getBoundingBox(space='world')
        return bb

    @classmethod
    def bb_sum(cls, *args):
        if not args:
            return dt.BoundingBox([-1,-1,-1],[1,1,1])
        def bbsum(b1, b2):
            return dt.BoundingBox([
                                   min(b1.min()[0], b2.min()[0]),
                                   min(b1.min()[1], b2.min()[1]),
                                   min(b1.min()[2], b2.min()[2])],
                                   [
                                   max(b1.max()[0], b2.max()[0]),
                                   max(b1.max()[1], b2.max()[1]),
                                   max(b1.max()[2], b2.max()[2])
                                   ])
        args = list(args)
        bb = args.pop(0)
        for b in args:
            bb = bbsum(bb, b)
        return bb

    def get_args(self):
        pass

    def build_rig(self, objs):
        pass

    def post_build(self, *args):
        pass

    @classmethod
    def create(cls, objs, parent=None):
        master = cls(parent)
        return master.build_rig(objs)


class CameraRig_Turntable(BaseRig):
    title = 'Turntable 360'
    groupName = 'turntable_camera_rig'
    camera_name = 'turntable_camera'
    def __init__(self, parent=None):
        super(CameraRig_Turntable, self).__init__()
        self.parent = parent

    def get_args(self):
        fr = QInputDialog.getInt(self.parent, 'Turntable Camera', 'Enter crame count', 179, min=3, max = 2147483647)
        if fr[1]:
            args = dict(
                frames = fr[0]
            )
            return args

    def build_rig(self, objs):
        data = self.get_args()
        if not data is None:
            root = self.create_root_group()
            cam = self.create_camera(objs, root, data['frames'])
            addAttr(cam, ln=self.cam_attr_name, dt='string')
            atr = {'range':[0,data['frames']]}
            cam.attr(self.cam_attr_name).set(json.dumps(atr))

            return cam, 0, data['frames']

    def create_camera(self, obj, parent=None, frames=179, clockwise=True, dolly=0):
        # turntable camera
        if isinstance(obj, list):
            bb = self.bb_sum(*[x.boundingBox() for x in obj])
        else:
            bb = obj.boundingBox()
        # boundBox(bb)
        rot = spaceLocator(name='rigTurnLocator')
        rot.t.set(bb.center())
        if clockwise:
            # fullDagPath=1
            expr = rot.ry.name()+'=frame*((360.0-(360.0/{0}))/{0})'.format(frames)
        else:
            expr = rot.ry.name()+'=(frame-2)*((-1)*(360.0-(360.0/{0}))/%s)' % frames
        ex = expression( s=expr, o=rot, a='ry', name='turntable1')
        rot.setParent(parent)
        rot.hide()
        y = bb.max()[1] - ( (bb.max()[1]-bb.min()[1])/3 )
        if bb.depth() > bb.width():
            pos = [max(bb.depth(), bb.width())*2, y, 0]
        else:
            pos = [0, y, max(bb.depth(), bb.width())*2]
        tr, persp_cam = camera(name=self.camera_name,worldCenterOfInterest =bb.center(), position=pos)
        persp_cam.nearClipPlane.set(1)
        persp_cam.farClipPlane.set(100000)
        persp_cam.focalLength.set(70)
        persp_cam.displayResolution.set(1)
        persp_cam.displayGateMask.set(1)
        tr.setParent(rot)
        select(obj)
        runtime.FrameSelectedInAllViews()
        if dolly:
            persp_cam.dolly(dolly, relative=True)
        return persp_cam


class CameraRig_OrtoView4(BaseRig):
    title='Orto View 2x2'
    groupName = 'ortoview4_camera_rig'
    camera_name = 'ortoview4_camera'
    def __init__(self, parent=None):
        super(CameraRig_OrtoView4, self).__init__()
        self.parent = parent

    # def get_args(self):
    #     pass

    def build_rig(self, objs):
        # args = self.get_args()
        root = self.create_root_group()
        cam, bounds = self.create_camera2(objs, root)
        addAttr(cam, ln=self.rig_attr_name, dt='string')
        cam.attr(self.rig_attr_name).set('orto')

        addAttr(cam, ln=self.cam_attr_name, dt='string')
        atr = {'range':[1,4]}
        cam.attr(self.cam_attr_name).set(json.dumps(atr))
        self.post_build(cam, bounds)
        return cam, 1, 4


    def create_camera(self, objs, parent=None, uber=True):
        # orto cameras
        bb = self.get_bounding_box(objs)
        cams = []
        offset = 30
        cameras = {'cam_left':{'t':bb.center() + dt.Point(bb.min()[2]-offset,0,0), 'r':dt.Vector([0.0, -90.0, 0.0])},
                   'cam_front':{'t':bb.center()+dt.Point(0,0,bb.max()[2]+offset), 'r':dt.Vector([0.0, 0.0, 0.0])},
                   'cam_top':{'t':bb.center()+dt.Point(bb.max()[0]+offset,0,0), 'r':dt.Vector([0.0, 90.0, 0.0])},
                   'cam_axo':{'t':bb.center()+dt.Point(0,0,bb.min()[2]-offset), 'r':dt.Vector([0.0, 180.0, 0.0])}
                  }

        for name, data in cameras.items():
            tr, cam = camera(name=name)
            tr.setParent(parent)
            cam.orthographic.set(1)
            cam.overscan.set(1)
            cam.displayResolution.set(1)
            cam.displayGateMask.set(1)
            tr.t.set(data['t'])
            tr.r.set(data['r'])
            lookThru(cam)
            select(objs)
            runtime.FrameSelectedInAllViews()
            o = cam.orthographicWidth.get()
            cam.orthographicWidth.set(o+(o*0.3))

            cams.append(cam)
            tr.hide()
        # collapse to single animated camera
        if uber:
            ftr, fcam = camera(name=self.camera_name)
            ftr.setParent(parent)
            fcam.orthographic.set(1)
            fcam.displayResolution.set(1)
            fcam.displayGateMask.set(1)
            fcam.overscan.set(1)
            widths = []
            for i, c in enumerate(cams):
                setCurrentTime(i)
                ftr.t.set(c.getParent().t.get())
                ftr.t.setKey()

                ftr.r.set(c.getParent().r.get())
                ftr.r.setKey()

                widths.append(c.orthographicWidth.get())
                # fcam.orthographicWidth.setKey()
            fcam.orthographicWidth.set(max(widths))
            delete([x.getParent() for x in cams])
            return fcam
        else:
            return cams

    def create_camera2(self, obj, root, guides=False):
        # obj = selected()
        poly_alpha = 0.1
        objs = [x for x in listRelatives(obj, allDescendents=1)+obj if x.type()=='transform' and hasattr(x, 'getShape') and x.getShape() and x.getShape().type() == 'mesh']
        # world bound
        wbb = self.get_bounding_box(objs)
        array = [
            dt.Vector(1,0,0),
            dt.Vector(0,1,0),
            dt.Vector(0,0,1),
            dt.Vector(1,1,1),
        ]

        ################################################################

        tr, sh = camera(name=self.camera_name)
        sh.orthographic.set(1)
        sh.displayResolution.set(1)
        sh.overscan.set(1)
        #cliping plane

        plane1 = polyPlane(ch=0, sx=1, sy=1 )[0]
        plane1.setParent(tr)
        plane1.setMatrix(dt.Matrix())
        plane1.rx.set(90)
        runtime.FreezeTransformations(plane1)
        plane2 = duplicate(plane1)[0]
        md = createNode('multiplyDivide')
        tr.nearClipPlane >> md.input1X
        tr.farClipPlane >> md.input1Y
        md.input2X.set(-0.99)
        md.input2Y.set(-1.01)
        md.outputX >> plane1.tz
        md.outputY >> plane2.tz
        polyColorPerVertex(plane1, r=1, g=0, b=0, a=poly_alpha, cdo=1)
        polyColorPerVertex(plane2, r=1, g=0, b=0, a=poly_alpha, cdo=1)

        mp = ui.PyUI(playblast(activeEditor=True))
        mp.setCamera(sh)
        lookThru(sh)
        bounds = createNode('transform', name='%s_guides' % tr.name())
        bounds.visibility >> plane1.visibility
        bounds.visibility >> plane2.visibility

        for i, a in enumerate(array):
            factor = 0.7
            currentTime(i+1)
                # camera bound
            a = -a.normal()
            pos = wbb.center() + -(a*(max(wbb.height(), wbb.width(), wbb.depth())))
            tr.t.set(pos)

            loc = spaceLocator()
            loc.t.set(wbb.center())
            aim = aimConstraint(loc, tr, offset=[0, 0, 0],
                                    weight=1, aimVector=[0,0,-1], upVector=[0, 1, 0],
                                    worldUpType="vector", worldUpVector=[0, 1, 0])
            mx_cam = tr.getMatrix(worldSpace=1)
            par = createNode('transform', name='temp')
            for o in objs:
                dup = duplicate(o)[0]
                dup.setParent(par)
            par.centerPivots()
            par.setMatrix(mx_cam.inverse())
            par.centerPivots()
            makeIdentity(par, apply=True )
        #    runtime.FreezeTransformations(par)
            cbb = self.get_bounding_box(par)
            delete(par)
            bbox = boundBox(cbb)
            bbox.centerPivots()
            bbox.setMatrix(mx_cam)
            polyColorPerVertex(bbox, r=0, g=1, b=0, a=poly_alpha, cdo=1)
            bbox.visibility.setKey(v=0, t=[i,i+2])
            bbox.visibility.setKey(v=1, t=[i+1,i+1])
            bbox.setParent(bounds)

            select(objs)
            viewFit(f=factor)
            sh.orthographicWidth.setKey()
            tr.t.setKey()
            tr.r.setKey()
            near = (pos.distanceTo(loc.getTranslation())-(cbb.depth()/2))*0.9
            far = (pos.distanceTo(loc.getTranslation())+(cbb.depth()/2))*2
            tr.nearClipPlane.set(near)
            tr.nearClipPlane.setKey()
            tr.farClipPlane.set(far)
            tr.farClipPlane.setKey()

            plane1.sy.set(cbb.height())
            plane1.sx.set(cbb.width())
            plane2.sy.set(cbb.height())
            plane2.sx.set(cbb.width())
            plane1.s.setKey()
            plane2.s.setKey()
            delete([loc, aim])
        tr.setParent(root)

        if not guides:
            delete([bounds, plane1, plane2])
        else:
            bounds.setParent(root)

        return sh, bounds

    def post_build(self, cam, guides):
        pass


def reset_viewport():
    for mp in getPanel(type=ui.Panel('modelPanel')):
        modelEditor(mp, edit=1, shadows=0, dl='default', dtx=1, udm=0, cameras=1, grid=1, lights=0, wireframeOnShaded=0)

rigs = [
    CameraRig_Turntable,
    CameraRig_OrtoView4
]