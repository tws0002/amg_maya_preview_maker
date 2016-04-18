from pymel.core import *
from .. import submitter_variables as v

special_attr_name = 'specialRigAttr' # copy to ogl.py
source_mesh_attr_name = 'sourceMesh'
oglEngineAttrName = 'submitterOglEngine'
layerSubmitterAttr = 'submitterLayer'
layerNameAttr = 'submitterLayerName'
hookAttrName = 'melHook'

class LayerManager(object):
    shader_name = 'original'
    use_ai_bg = True
    ai_diffuse_bounce = None
    duplicate_group_name = None
    ogl_engine = 'blast'
    ogl_ao = True
    mel_callback_on = ''
    mel_callback_off = ''

    def __init__(self):
        super(LayerManager, self).__init__()
        self.shader_name = self.__class__.shader_name
        # if self.shader_name == DEFAULT_SHADER:
        #     self.layer_name = 'defaultRenderLayer'
        # else:
        self.layer_name = self.shader_name
        self.shader = self.find_shader(self.shader_name)
        self.layer = self.find_layer(self.layer_name)
        self.layer_enabled = True
        self.ai_bg = None

        #other
        self.bg_color = None

    def create_layer(self):
        self.layer = create_render_layer(self.layer_name)
        if self.mel_callback_on:
            addAttr(self.layer, ln=hookAttrName, dt='string')
            self.layer.attr(hookAttrName).set(self.mel_callback_on)
        # submitter attr
        addAttr(self.layer, ln=layerSubmitterAttr, at='message')
        if self.shader_name.startswith('ogl'):
            addAttr(self.layer, ln=oglEngineAttrName, dt='string')
            self.layer.attr(oglEngineAttrName).set(self.ogl_engine)

        for tp, ls in shaders.items():
            for sh in ls:
                if sh['func'] == self.__class__:
                    addAttr(self.layer, ln=layerNameAttr, dt='string')
                    self.layer.attr(layerNameAttr).set(sh['title'])

        if self.layer:
            self.layer.setCurrent()
            if not self.ai_diffuse_bounce is None:
                ar = PyNode('defaultArnoldRenderOptions')
                self.layer.addAdjustments(ar.GIDiffuseSamples)
                evalDeferred('from maya import cmds;cmds.setAttr("%s.GIDiffuseSamples", %s)' % (ar.name(), self.ai_diffuse_bounce))

    def update_layer_objects(self, to_include, to_shade, remove_studio=False, remove_background=False, applyShader=True):
        if not self.layer or self.layer.name() == 'defaultRenderLayer':
            return
        if remove_background:
            to_include = [x for x in to_include if not x.hasAttr(v.submitter_rig_attribute_name) or not x.attr(v.submitter_rig_attribute_name).get() in ['env', 'ground']]

        if remove_studio:
            to_include = to_shade
        self.layer.addMembers([x for x in to_include if x.exists()])

        if applyShader:
            if not self.shader:
                self.shader = self.find_shader(self.shader_name)
            if self.get_shader():# and not self.shader_name == DEFAULT_SHADER:
                s = self.get_shader()
                if s and not s is True:
                    # l = PyNode(editRenderLayerGlobals( query=True, currentRenderLayer=True ))
                    l = nt.RenderLayer.currentLayer()
                    self.layer.setCurrent()
                    editRenderLayerGlobals( enableAutoAdjustments=True )
                    sets(s.shadingGroups()[0], forceElement=to_shade)
                    l.setCurrent()

        if not self.use_ai_bg and self.shader_name.startswith('ai_'):
            airender = PyNode('defaultArnoldRenderOptions')
            ai_bg = airender.background.get()
            if ai_bg and ai_bg.hasAttr('intensity'):
                self.layer.addAdjustments(ai_bg.intensity)
                ai_bg.intensity.set(0)

    def remove_layer(self):
        if self.layer:# and not self.layer_name == 'defaultRenderLayer':
            mel.renderLayerEditorDeleteLayer('RenderLayerTab', self.layer)
        # else:
        #     if self.layer:
        #         self.layer.renderable.set(0)

    def update_layer(self):
        if self.layer:
            self.layer.setCurrent()
            if self.shader and not isinstance(self.shader, bool):
                select(self.shader)
            self.update_script()
            # return True
        else:
            PyNode('defaultRenderLayer').setCurrent()
            # warning('Layer not exists')
            # return False

    def disable_layer(self, restore_background=False):
        if restore_background and self.bg_color:
            ogl_black_background(False, self.bg_color)


    def find_shader(self, name):
        return ([x for x in ls(materials=True) if x.stripNamespace() == name] or [None])[0]

    def find_layer(self, name):
        # if name == 'defaultRenderLayer':return PyNode('defaultRenderLayer')
        return (ls(v.render_layer_prefix+name, type='renderLayer') or [None])[0]

    def update_script(self):
        pref = self.__class__.__name__.split('_')[0]
        script = v.join(v.scenes_root, '%s.py' % pref)
        if os.path.exists(script):
            execfile(script)

    def get_shader(self):
        if self.shader is True:
            return True
        if self.shader and not isinstance(self.shader, bool):
            return self.shader

    def preview_name(self):
        if objExists(str(self.shader)):
            return (self.shader.stripNamespace() + '.png').replace('\\','/')

    def getSurfaceShader(self, objName, sg=True):
        l = nt.RenderLayer.currentLayer()
        # nt.RenderLayer.defaultRenderLayer().setCurrent()
        shape = objName.getShape()
        if shape:
            groups = shape.outputs(type='shadingEngine')
            if sg:
                l.setCurrent()
                return groups
            else:
                shaders = []
                for g in groups:
                    shaders+=g.surfaceShader.inputs()
                # l.setCurrent()
                return shaders
        # l.setCurrent()

    def getMembers(self, sg):
        members = []
        for x in sg.members():
             if type(x) == general.MeshFace:
                 members.append(x)
             if type(x) == nodetypes.Mesh and objExists(x):
                 members.append(x)
        return members

    def replaceShader(self, sg, shader='lambert', parms=None):
        mem = self.getMembers(sg)
        sh = sg.surfaceShader.inputs()[0]
        news, newg = createSurfaceShader(shader, name = sh.name()+'_replaced')
        src = sh.attr('color') if sh.hasAttr('color') else sh.attr('outColor')
        trg = news.attr('color') if news.hasAttr('color') else news.attr('outColor')
        self.copyAttrInputs(src, trg, connect = True)

        sets(newg, forceElement=mem)
        if parms:
            for parm, val in parms.items():
                if news.hasAttr(parm):
                    news.attr(parm).set(val)
        return news, newg

    def copyAttrInputs(self, from_attr, to_attr, connect=False, root=True):
        connected = False
        if from_attr.inputs():
            from_attr.inputs(p=1)[0] >> to_attr
            return True
        elif from_attr.isCompound() and to_attr.isCompound():
            frc = from_attr.children()
            toc = to_attr.children()
            for i in range(max([len(frc), len(toc)])):
                result = self.copyAttrInputs(frc[i], toc[i], root=False)
                connected = connected or result
        if not connected and root:
            from_attr >> to_attr

    def use_scele_ligths(self, use=True):
        for mp in getPanel(type=ui.Panel('modelPanel')):
            modelEditor(mp, edit=1, dl='all' if use else 'default', shadows=1, dtx=1, udm=0, cameras=0, grid=0, lights=0, wireframeOnShaded=0)

# Arnold ###############################################################################################################

class ai_original(LayerManager):
    mel_callback_on = '''python("from pymel.core import *;PyNode('defaultArnoldDriver').gamma.set(2.2**2)")'''

    def create_layer(self):
        super(ai_original, self).create_layer()
        if self.layer:
            ar = PyNode('defaultArnoldDriver')
            self.layer.setCurrent()
            self.layer.addAdjustments(ar.gamma)
            ar.gamma.set(2.2**2)

class ai_flat_diffuse(LayerManager):
    shader_name='ai_flat_shader'
    use_ai_bg=False
    ai_diffuse_bounce = 0
    def __init__(self):
        super(ai_flat_diffuse, self).__init__()
        self.shaders = []

    def update_layer_objects(self, to_include, to_shade, remove_studio=False, remove_background=False, applyShader=False):
        super(ai_flat_diffuse, self).update_layer_objects(to_include, to_shade, remove_studio=True, remove_background=True, applyShader=False)
        if self.layer:
            self.layer.setCurrent()
            # objs = [x for x in listRelatives(to_shade, allDescendents =1) if hasattr(x,'getShape') and x.getShape()]
            objs = [x.getParent() for x in listRelatives(to_shade, allDescendents =1) if x.type() == 'mesh']
            sGroups = []
            for obj in objs:
                sg = self.getSurfaceShader(obj)
                if sg:
                    sGroups+=sg
            sGroups = list(set(sGroups))
            for sh in sGroups:
                shd = sh.surfaceShader.inputs()[0]
                s, g = self.replaceShader(sh, 'aiUtility', {'shadeMode':2})
                # s, g = self.replaceShader(sh, 'surfaceShader')
                # color convert
                if s.color.inputs():
                    if s.color.inputs()[0].name() == shd.name():
                        st, _gr = createSurfaceShader('aiStandard', name=s.name()+'_conv')
                        s.color.inputs(p=1)[0] >> st.color
                        st.color >> s.color
                        delete(_gr)
                        self.shaders.append(st)
                self.shaders.append(s)
                self.shaders.append(g)

    def remove_layer(self):
        super(ai_flat_diffuse, self).remove_layer()
        # delete(self.light)
        delete(self.shaders)

    # def create_layer(self):
    #     super(ai_flat_diffuse, self).create_layer()
    #     if self.layer:
    #         ar = PyNode('defaultArnoldRenderOptions')
    #         self.layer.setCurrent()
    #         self.layer.addAdjustments(ar.GIDiffuseSamples)
    #         evalDeferred('from maya import cmds;cmds.setAttr("%s.GIDiffuseSamples", 0)' % ar.name())

class ai_wireframe(LayerManager):
    shader_name='ai_wireframe'
    use_ai_bg=False
    ai_diffuse_bounce = 0

    def update_layer_objects(self, to_include, to_shade, **kwargs):
        super(ai_wireframe, self).update_layer_objects(to_include, to_shade, remove_studio=True, remove_background=True)

class ai_ambient_occlusion(LayerManager):
    shader_name='ai_ambient_occlusion'
    ai_diffuse_bounce = 0

    def update_layer_objects(self, *args, **kwargs):
        super(ai_ambient_occlusion, self).update_layer_objects(*args, **kwargs)
        if self.layer:
            airender = PyNode('defaultArnoldRenderOptions')
            ai_bg = airender.background.get()
            if ai_bg:
                self.layer.addMembers(ai_bg)
                self.layer.addAdjustments(ai_bg.color)
                if ai_bg.color.inputs(p=1):
                    ai_bg.color.inputs(p=1)[0].disconnect(ai_bg.color)
                ai_bg.color.set(1,1,1)
            ground = None
            for ref in listReferences():
                objs = [x for x in ref.nodes() if x.hasAttr(v.submitter_rig_attribute_name)]
                for o in objs:
                    if o.attr(v.submitter_rig_attribute_name).get() == 'ground':
                        ground = o
                        break
                if ground:
                    break
            if ground:
                self.layer.setCurrent()
                sets(self.shader.shadingGroups()[0], forceElement=ground)

class ai_uv_flat(LayerManager):
    shader_name='ai_uv_flat'
    use_ai_bg=False
    ai_diffuse_bounce = 0

    def update_layer_objects(self, to_include, to_shade, **kwargs):
        super(ai_uv_flat, self).update_layer_objects(to_include, to_shade, remove_studio=True, remove_background=True)

class ai_falloff(LayerManager):
    shader_name='ai_falloff'
    use_ai_bg=False
    ai_diffuse_bounce = 0

    def update_layer_objects(self, to_include, to_shade,  **kwargs):
        super(ai_falloff, self).update_layer_objects(to_include, to_shade, remove_studio=True, remove_background=True)

# OpenGL ###############################################################################################################

class ogl_original(LayerManager):
    ogl_ao = True

class ogl_diffuse_flat(LayerManager):
    shader_name='ogl_diffuse_flat'
    ogl_ao = False
    def __init__(self):
        super(ogl_diffuse_flat, self).__init__()
        self.shader = True
        self.shaders = []
        self.light = None

    def create_layer(self):
        super(ogl_diffuse_flat, self).create_layer()
        # if not hasattr(self, 'jobNum'):
        #     self.jobNum = None
        if objExists('ogl_flatlight'):
            self.light = PyNode('ogl_flatlight')
        else:
            self.light = nt.AmbientLight(name='ogl_flatlight').getParent()
        self.light.color.set(0,0,0)
        add_spec_attr(self.light)
        self.light.setParent(v.root_group())
        self.layer.addMembers([self.light])
        self.layer.setCurrent()
        self.layer.addAdjustments(self.light.color)
        self.light.color.set([1,1,1])

        # self.jobNum = cmds.scriptJob( event= ["renderLayerManagerChange",self.layer_changed])
        # scriptJob( kill=jobNum, force=True)

    def layer_changed(self, light, layer):
        self.light.visibility.set(PyNode(editRenderLayerGlobals( query=True, currentRenderLayer=True )).name() == self.layer)

    def remove_layer(self):
        super(ogl_diffuse_flat, self).remove_layer()
        delete(self.light)
        delete(self.shaders)

    def update_layer_objects(self, to_include, to_shade, remove_studio=False, remove_background=False, applyShader=False):
        to_include += [x for x in listRelatives(to_include, allDescendents =1) if hasattr(x,'getShape') and x.getShape()]
        to_shade += [x for x in listRelatives(to_shade, allDescendents =1) if hasattr(x,'getShape') and x.getShape()]
        to_include+=[x.getShape() for x in to_include if hasattr(x,'getShape') and x.getShape()]
        # exclude lights
        lights = ls(to_include, lights=1)
        lights += [x.getParent() for x in lights]
        to_include = [x for x in to_include if not x in lights]
        super(ogl_diffuse_flat, self).update_layer_objects(to_include, to_shade, remove_studio=True, remove_background=True, applyShader=False)
        if self.layer:
            self.layer.setCurrent()
            objs = [x for x in listRelatives(to_shade, allDescendents =1) if hasattr(x,'getShape') and x.getShape()]
            sGroups = []
            for obj in objs:
                sg = self.getSurfaceShader(obj)
                if sg:
                    sGroups+=sg
            sGroups = list(set(sGroups))
            for sh in sGroups:
                new = self.replaceShader(sh)
                self.shaders+=list(new)

    def update_layer(self):
        super(ogl_diffuse_flat, self).update_layer()
        PyNode('hardwareRenderingGlobals').ssaoEnable.set(self.ogl_ao)
        wireframe(False)
        self.use_scele_ligths()
        self.bg_color = ogl_black_background()

    def disable_layer(self, **kwargs):
        super(ogl_diffuse_flat, self).disable_layer(restore_background=True)

    def preview_name(self):
        return self.shader_name+'.png'

class ogl_wireframe_shaded(LayerManager):
    shader_name='ogl_wireframe_shaded'
    duplicate_group_name = 'ogl_wire_shade'
    wireColor = (0,0,0)
    ogl_ao = False
    ogl_engine = 'hw'
    def __init__(self):
        super(ogl_wireframe_shaded, self).__init__()
        self.wire_folder = None
        self.jobs = []

    def update_layer(self):
        super(ogl_wireframe_shaded, self).update_layer()
        self.bg_color = ogl_black_background()
        wireframe(False)
        PyNode('hardwareRenderingGlobals').ssaoEnable.set(self.ogl_ao)
        for mp in getPanel(type=ui.Panel('modelPanel')):
            modelEditor(mp, edit=1, dl="default", shadows=0, dtx=1)

    def update_layer_objects(self, to_include, to_shade, **kwargs):
        kwargs['remove_background'] = True
        super(ogl_wireframe_shaded, self).update_layer_objects(to_include,to_shade, **kwargs)
        if not self.layer:
            return
        path = v.root_group().name()+'|'+ self.duplicate_group_name
        if objExists(path):
            self.wire_folder = PyNode(path)
        else:
            self.wire_folder = createNode('transform', name=self.duplicate_group_name, parent=v.root_group())
        select(cl=1)
        wire_objects = []

        wireVisAttr = 'showWireFrame'
        if self.shader:
            if self.shader.type() == 'cgfxShader':
                if not self.shader.hasAttr(wireVisAttr):
                    addAttr(self.shader, ln=wireVisAttr, at='bool')
                self.shader.attr(wireVisAttr) >> self.wire_folder.visibility

        if self.shader:
            wireAttrName = 'wireColor'
            sh = self.shader
            if self.shader.hasAttr('select'):
                if self.shader.select.inputs():
                    sh = self.shader.select.inputs()[0]
            if not sh.hasAttr(wireAttrName):
                addAttr(sh, ln=wireAttrName, at='float3', uac=1)
                addAttr(sh, ln=wireAttrName+"X",at="float", p=wireAttrName)
                addAttr(sh, ln=wireAttrName+"Y",at="float", p=wireAttrName)
                addAttr(sh, ln=wireAttrName+"Z",at="float", p=wireAttrName)
                # sh.wireColor.set(self.wireColor)
                sh.wireColor.setKeyable(1)
        else:
            sh = None
        for x in listRelatives(to_shade, allDescendents =1):
            if x and x.type() == 'mesh':
                src = x.getParent()
                src.overrideEnabled.set(0)
                if self.wire_folder in [x.node().getParent() for x in [x for x in src.message.outputs(p=1) if x.name().split('.')[-1] == 'sourceMesh']]:
                    continue
                d = duplicate(src)[0]
                d.renderLayerInfo.disconnect()
                d.setParent(self.wire_folder)
                wire_objects.append(d)

                d.overrideEnabled.set(1)
                d.overrideShading.set(0)
                # d.overrideRGBColors.set(0)
                # d.overrideColor.set(self.wireColor)
                d.overrideRGBColors.set(1)
                blendShape(src, d, origin ='world', weight=[0,1])
                self.jobs.append(scriptJob(kws=1, ac=[src.displaySmoothMesh,lambda:d.displaySmoothMesh.set(src.displaySmoothMesh.get())]))

                if not d.hasAttr(source_mesh_attr_name):
                    addAttr(d, ln=source_mesh_attr_name, at='message')
                src.message >> d.attr(source_mesh_attr_name)
                if sh:
                    sh.wireColor >> d.overrideColorRGB
                else:
                    d.overrideColorRGB.set(self.wireColor)


        if self.layer:
            self.layer.addMembers(wire_objects)
        # for src in wire_objects:
        #     # sets(PyNode('initialShadingGroup'), forceElement=d)

    def remove_layer(self):
        super(ogl_wireframe_shaded, self).remove_layer()
        if self.wire_folder and objExists(self.wire_folder):
            delete(self.wire_folder)
            return
        grp = '|'.join([v.root_group_name,self.duplicate_group_name])
        if objExists(grp):
            delete(PyNode(grp))
        ogl_black_background(False)
        map(lambda x:scriptJob(kill=x), self.jobs)

class ogl_wireframe_flat(ogl_wireframe_shaded):
    shader_name='ogl_wireframe_flat'
    duplicate_group_name = 'ogl_wire_flat'
    wireColor = 2
    ogl_engine = 'hw'
    ogl_ao = False

class ogl_debug(LayerManager):
    shader_name = 'ogl_debug'
    duplicate_group_name = 'debug_grp'
    wireColor = 15
    ogl_engine = 'blast'
    ogl_ao = False

    def create_layer(self):
        super(ogl_debug, self).create_layer()
        if self.shader:
            self.shader.technique.set("SimpleWithFresnel")
            gfx_file = os.path.join(os.path.dirname(os.path.dirname(__file__)),'lib', 'shaders', 'debug.cgfx').replace('\\','/')
            if os.path.exists(gfx_file):
                mel.cgfxShader(self.shader, e=1, fx=gfx_file)
            else:
                warning('GFX SHADER NO FOUND!!!')
        else:
            print 'shader not found', self.shader_name

    def update_layer_objects(self, to_include, to_shade, **kwargs):
        kwargs['remove_background'] = True
        super(ogl_debug, self).update_layer_objects(to_include,to_shade, **kwargs)

    def update_layer(self):
        super(ogl_debug, self).update_layer()
        self.bg_color = ogl_black_background()
        wireframe(False)
        PyNode('hardwareRenderingGlobals').ssaoEnable.set(0)
        for mp in getPanel(type=ui.Panel('modelPanel')):
            modelEditor(mp, edit=1, dl="default", shadows=0, dtx=1)

class ogl_flat_uv(LayerManager):
    shader_name='ogl_flat_uv'
    ogl_ao = False
    def update_layer_objects(self, to_include, to_shade, **kwargs):
        super(ogl_flat_uv, self).update_layer_objects(to_shade,to_shade, **kwargs)

    def update_layer(self):
        super(ogl_flat_uv, self).update_layer()
        for mp in getPanel(type=ui.Panel('modelPanel')):
            modelEditor(mp, edit=1, dl="default", shadows=0, dtx=1)
        PyNode('hardwareRenderingGlobals').ssaoEnable.set(self.ogl_ao)
        self.bg_color = ogl_black_background()
        wireframe(False)

    def create_layer(self):
        super(ogl_flat_uv, self).create_layer()
        if self.shader:
            color = self.shader.outColor.inputs()
            txd = None
            if color:
                if color[0].type() == 'file':
                    txd = color[0]
            else:
                txd = PyNode(mel.eval('createRenderNodeCB -as2DTexture "" file "";'))
                txd.rename('ogl_flat_uv_texture')
            if txd:
                for ch in self.shader.outColor.children():
                    ch.disconnect()
                if os.path.exists(v.uv_checher_texture):
                    txd.fileTextureName.set(v.uv_checher_texture)
                else:
                    txd.defaultColor.set(1,0,0)
                txd.outColor >> self.shader.outColor

    def disable_layer(self, **kwargs):
        super(ogl_flat_uv, self).disable_layer(restore_background=True)
        ogl_black_background(False)

class ogl_ambient_occlusion(LayerManager):
    shader_name='ogl_ambient_occlusion'
    ogl_ao = True
    def update_layer(self):
        super(ogl_ambient_occlusion, self).update_layer()
        for mp in getPanel(type=ui.Panel('modelPanel')):
            modelEditor(mp, edit=1, dl="default", shadows=0, dtx=1)
        PyNode('hardwareRenderingGlobals').ssaoEnable.set(self.ogl_ao)
        wireframe(False)

class ogl_falloff(LayerManager):
    shader_name='ogl_falloff'
    ogl_ao = False
    def update_layer_objects(self, to_include, to_shade, **kwargs):
        super(ogl_falloff, self).update_layer_objects(to_shade,to_shade, **kwargs)

    def update_layer(self):
        super(ogl_falloff, self).update_layer()
        for mp in getPanel(type=ui.Panel('modelPanel')):
            modelEditor(mp, edit=1, dl="default", shadows=0, dtx=1)
        PyNode('hardwareRenderingGlobals').ssaoEnable.set(self.ogl_ao)
        self.bg_color = ogl_black_background()
        wireframe(False)

    def disable_layer(self, **kwargs):
        super(ogl_falloff, self).disable_layer(restore_background=True)

######### LIST

shaders = dict(
    ai=[
        dict(title='Derault',
             func=ai_original),
        dict(title='Flat Diffuse',
             func=ai_flat_diffuse),
        dict(title='Ambient Occlusion',
             func=ai_ambient_occlusion),
        dict(title='UV',
             func=ai_uv_flat),
        dict(title='Falloff',
             func=ai_falloff),
        dict(title='Wireframe',
             func=ai_wireframe),
    ],
    ogl=[
        dict(title='Default',
             func=ogl_original),
        dict(title='Diffuse Flat',
             func=ogl_diffuse_flat),
        dict(title='Wireframe Flat',
             func=ogl_wireframe_flat),
        dict(title='Wireframe Shaded',
             func=ogl_wireframe_shaded),
        dict(title='UV',
             func=ogl_flat_uv),
        dict(title='Ambient Occlusion',
             func=ogl_ambient_occlusion),
        dict(title='Falloff',
             func=ogl_falloff),
        dict(title='Debug Two Side',
             func=ogl_debug),
    ]
)

######### funcs

def create_render_layer(name):
    select(cl=1)
    ly = createRenderLayer(name=v.render_layer_prefix+name)
    ly.setCurrent()
    editRenderLayerGlobals( enableAutoAdjustments=True )
    return ly

def add_spec_attr(obj):
    if not obj.hasAttr(special_attr_name):
        addAttr(obj, ln=special_attr_name, dt='string')

def ogl_black_background(on=True, color=None):
    if on:
        color = color or (0,0,0)
        rgb = displayRGBColor('background', query=1)
        displayRGBColor('background', *color)
        displayPref(displayGradient=0)
        return rgb
    else:
        if optionVar["displayViewportGradient"]:
            displayPref(displayGradient=1)
        if color:
            displayRGBColor('background', *color)

def wireframe(enable=True):
    for mp in getPanel(type=ui.Panel('modelPanel')):
        modelEditor(mp, edit=1, wireframeOnShaded=enable)

