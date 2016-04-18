import os

try:
    import sgtk
    from tank_vendor.shotgun_authentication import ShotgunAuthenticator
    from amg.shotgun import amg_shoutgun
    reload(amg_shoutgun)
    is_valid = True
except:
    is_valid = False

folder_map = {'Anm': 'Anim', 'Model':'mdl'}

def join(*args):
    return '/'.join([str(x) for x in args]).replace('\\','/')



def is_active():
    return os.environ.get('TANK_CURRENT_PC').replace('\\','/')

def publish_preview(src_path):
    # src_path = 'D:/work/amg/projects/dev/sequences/EP001/SH001/Anim/work/maya/scene1.mb'.replace('/','\\')
    trg_path = 'D:/work/amg/projects/dev/sequences/EP001/SH001/Anim/work/maya/scene1.mb'.replace('/','\\')

    sa = ShotgunAuthenticator()
    user = sa.create_script_user(api_script="Toolkit",
                                 api_key="2062d7c5d64ad72552fb0e983bd25203a823580620410a56367ac491d325fc6f",
                                 host="https://animagrad.shotgunstudio.com")
    sgtk.set_authenticated_user(user)

    tk = sgtk.sgtk_from_path(trg_path)
    ctx = tk.context_from_path(trg_path)
    publish_name = os.path.splitext(os.path.basename(src_path))[0]
    # thumbnail_path = path (545x300)
    try:
        sgtk.util.register_publish(tk, ctx, src_path, publish_name, 3)
        return True
    except:
        return False

def review_folder(scene, ctx=None):
    ctx = ctx or sg_context()
    tk = sgtk.sgtk_from_path(scene)
    return join(tk.paths_from_entity(ctx.entity['type'], ctx.entity['id'])[0], folder_map.get(ctx.step['name'], ctx.step['name']), 'review')

def sg_context():
    return amg_shoutgun.SG.current_context()

def context():
    ctx = sg_context()
    if not ctx.entity:
        return {}
    c = dict(
        project=ctx.project.get('name','-'),
        entity=ctx.entity.get('type','-').lower() if ctx.entity else '-',
        name= ctx.entity.get('name', '-') if ctx.entity else '-',
        step=ctx.step.get('name','-') if ctx.step else '-',
        task=ctx.task.get('name','-') if ctx.task else '-',
        sequence=''
    )
    if c['entity'] == 'shot':
        c['sequence'] = amg_shoutgun.SG_Shot(ctx.entity['id']).sequence().name
    return c

# tk.project_path
# tk.create_filesystem_structure
# tk.synchronize_filesystem_structure
# tk.preview_filesystem_structure()