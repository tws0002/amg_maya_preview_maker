import os
import pymel.core as pm
def join(*args):
    return '/'.join([str(x) for x in args]).replace('\\','/').replace('/','/')

def root_group( remove=False):
    if remove:
        node = root_group()
        if node:
            pm.delete(node)
    else:
        if pm.objExists(root_group_name):
            return pm.PyNode(root_group_name)
        else:
            return pm.createNode('transform', name=root_group_name)

submitter_namespase = 'submitter'
prefix = 'preview_submitter_'
render_layer_prefix = 'submitter_layer_'
res_orto = [(1000, 1000), (2000, 2000), (3000, 3000)]
# res_orto_redault = [1000,1000]
res_repsp = [(640, 360), (960, 540), (1280, 720), (1920, 1080)]
res_default = [1280, 720]

scenes_root = join(os.path.dirname(__file__),'lib','scenes')
shaders_root = join(os.path.dirname(__file__),'lib','shaders')
hdr_root = join(os.path.dirname(__file__),'lib','hdr')
txd_root = join(os.path.dirname(__file__),'lib','txd')
preview_images = shaders_root

object_set_name = 'preview_maker_objects'
root_group_name = 'preview_maker_grp'
submitter_rig_attribute_name = 'submitterObjType'
submitter_scale_attribute_name = "submitterScaleFactor"
session_id_node_name = 'submitter_session_id'
session_id_attrib = 'SessionId'
# outpyt types
IMAGES=0
SEQUENCE=1

ai_script = join(os.path.dirname(__file__), 'lib', 'scenes', 'ai.py')
ogl_script = join(os.path.dirname(__file__), 'lib', 'scenes', 'ogl.py')

uv_checher_texture = join(txd_root, 'uv_checker.jpg')
shaders_scene_name = 'shaders.ma'