from PySide.QtCore import *
from PySide.QtGui import *
from pymel.core import *
from pymel import mayautils
import maya.OpenMayaUI as omui
from shiboken import wrapInstance as wrp
import os, getpass, json, tempfile, random, datetime, shutil
from widgets import submitter_window_UIs, shader_list, preview_widget, stamp_options_window, confirm_gialog, render_blocks
from tools import camera_rig, object_set, shaders,  af_func, json_tools, shutgun_submit
from renderer import render_ai, render_ogl
import config
try:
    from amg.af import af_util
    af_is_valid = True
except:
    af_is_valid = False

reload(submitter_window_UIs)
reload(shader_list)
reload(preview_widget)
reload(stamp_options_window)
reload(confirm_gialog)
reload(camera_rig)
reload(object_set)
reload(shaders)
reload(render_ai)
reload(render_ogl)
reload(json_tools)
reload(shutgun_submit)
reload(render_blocks)
reload(config)

amg_sender = False
try:
    from amg_launcher import cmd_sender as amg_sender
except:
    warning('AMG Sender not found')

def getMayaWindow():
    ptr = omui.MQtUtil.mainWindow()
    if ptr is not None:
        return wrp(long(ptr), QMainWindow)
qMaya = getMayaWindow()

import submitter_variables as v
from submitter_variables import join
reload(v)

version = '1.0'
emptyField = ''

conf = dict(
    max_files_to_publish=10
)
TAB_AI = 0
TAB_OGL = 1


class SubmitterWindowClass(QMainWindow, submitter_window_UIs.Ui_MainWindow):
    def __init__(self):
        super(SubmitterWindowClass, self).__init__(qMaya)
        self.setupUi(self)
        # self.logo_btn.setIconSize(QSize(100,54))
        self.setWindowTitle('ANIMAGRAD | Preview Maker v'+version)
        self.ai_shaders = shader_list.ShaderListClass('ai', self)
        self.ai_shaders_ly.addWidget(self.ai_shaders)

        self.ogl_shaders = shader_list.ShaderListClass('ogl', self)
        self.ogl_shaders_ly.addWidget(self.ogl_shaders)

        self.stamp_opt_window = stamp_options_window.FrameStampOptions(self)
        self.stamp_opt_window.dataChangedSignal.connect(self.update_previewer_stamp_data)

        self.blocks = render_blocks.RenderBocksClass(self)
        self.blocks_ly.addWidget(self.blocks)

        self.ortoCam = None
        self.perspCam = None
        self.camRig = None
        self.customCameras = []
        self.current_ref_scene = None
        self.previewWidget = None
        self.previewGeo = None
        self.is_asset = False
        self.session_id = self.create_session_id()
        self.global_output = None
        self.global_output = self.global_output_folder()
        self.group_block = 0
        if shutgun_submit.is_valid:
            self.ctx = shutgun_submit.context()
        else:
            self.ctx = None

        self.bg_color = displayRGBColor('background', query=1)
        self.viewport_gradient = optionVar["displayViewportGradient"]
        self.renderer = ''

        self.define_current_scene()
        if self.current_ref_scene:
            self.add_light_preset_cbx.setChecked(1)
        self.init_shaders_scene()
        self.init_ui()
        self.blocks.update_from_folder(self.global_output)
        self.update_ui()
        # connect
        self.renderer_tab_tbw.currentChanged.connect(self.renderer_tab_changed)
        self.reload_cameras_btn.clicked.connect(self.update_exists_cameras)
        self.ai_scene_preset_cbb.currentIndexChanged.connect(self.update_hdr)
        self.ogl_scene_preset_cbb.currentIndexChanged.connect(self.load_ogl_scene)
        self.reload_rig_btn1.clicked.connect(self.rebuild_rig)
        self.reload_rig_btn2.clicked.connect(self.rebuild_rig)
        self.submit_btn.clicked.connect(self.submit_blocks)
        self.cleanup_scene_act.triggered.connect(self.cleanup_scene)
        self.ai_use_ground_plane_cbx.clicked.connect(self.show_hide_ground_plane)
        self.ogl_use_ground_plane_cbx.clicked.connect(self.show_hide_ground_plane)
        self.ai_ground_plane_texture_cbb.currentIndexChanged.connect(self.set_ground_texture)
        self.ogl_ground_plane_texture_cbb.currentIndexChanged.connect(self.set_ground_texture)
        self.add_objects_btn.clicked.connect(self.add_objects_to_set)
        self.remove_objects_btn.clicked.connect(self.remove_objects_from_set)
        self.select_objects_btn.clicked.connect(self.select_objects_in_set)
        self.clear_objects_btn.clicked.connect(self.delete_object_set)
        self.preview_frame_btn.clicked.connect(self.open_preview)
        self.ai_render_background_cbx.clicked.connect(self.connect_aiSky)
        self.stamp_options_btn.clicked.connect(self.open_stamp_options)
        self.open_sequence_editor_btn.clicked.connect(mel.SequenceEditor)
        self.create_new_camera_btn.clicked.connect(self.create_new_camera_rig)
        self.add_block_btn.clicked.connect(self.export_blocks)
        self.reload_blocks_btn.clicked.connect(lambda :self.blocks.update_from_folder(self.global_output))
        self.add_light_preset_cbx.clicked.connect(self.renderer_tab_changed)
        self.clear_blocks_btn.clicked.connect(self.clear_blocks)

        self.output_path_le.setContextMenuPolicy(Qt.CustomContextMenu)
        self.output_path_le.customContextMenuRequested.connect(self.out_path_custom_menu)
        self.stamp_asset_date_le.setContextMenuPolicy(Qt.CustomContextMenu)
        self.stamp_asset_date_le.customContextMenuRequested.connect(self.date_field_custom_menu)
        self.stamp_squens_date_le.setContextMenuPolicy(Qt.CustomContextMenu)
        self.stamp_squens_date_le.customContextMenuRequested.connect(self.date_field_custom_menu)

        #
        self.default_ui()
        for le in ( self.stamp_asset_project_le,self.stamp_asset_name_le,
                    self.stamp_asset_step_le,self.stamp_asset_task_le,
                    self.stamp_asset_user_le, self.stamp_asset_version_le,
                    self.stamp_asset_date_le, self.stamp_asset_date_le,
                    self.stamp_squens_name_le, self.stamp_squens_task_le,
                    self.stamp_squens_version_le, self.stamp_squens_step_le,
                    self.stamp_squens_shot_le, self.stamp_squens_project_le,
                    self.stamp_squens_user_le):
            le.editingFinished.connect(self.update_previewer_stamp_data)
        self.stamp_mode_asset_rb.clicked.connect(self.update_previewer_stamp_data)
        self.stamp_mode_shot_rb.clicked.connect(self.update_previewer_stamp_data)
        self.stamp_asset_frame_cbx.clicked.connect(self.update_previewer_stamp_data)
        self.add_frame_stamp_cbx.clicked.connect(self.update_previewer_stamp_data)
        self.render_camera_cbb.currentIndexChanged.connect(self.update_ui_from_camera)
        self.splitter.setSizes([560,self.width()-560])
        __import__('__main__').__dict__['asm'] = self

######################################## REIMPLEMENT

    def closeEvent(self, event):
        self.save_var()
        if self.previewWidget:
            self.previewWidget.deleteLater()
            self.previewWidget.close()
        self.stamp_opt_window.close()
        self.stamp_opt_window.deleteLater()
        if self.global_output:
            if not os.listdir(self.global_output):
                shutil.rmtree(self.global_output)
        super(SubmitterWindowClass, self).closeEvent(event)

################################### INIT AND CLOSE

    def init_ui(self):
        self.persp_res_cbb.clear()
        for i in v.res_repsp:
            self.persp_res_cbb.addItem('%sx%s' % i)
        self.persp_res_cbb.setCurrentIndex(2)

        self.update_exists_cameras()
        self.update_exists_ai_scenes()
        self.update_exists_ogl_scenes()
        # load shaders
        self.renderer_tab_changed()
        self.update_exists_textures()

        self.range_start_sbx.setValue(env.getAnimStartTime())
        self.range_end_sbx.setValue(env.getAnimEndTime())
        if shutgun_submit.is_valid:
            if self.ctx and sceneName():
                self.output_path_le.setText(shutgun_submit.review_folder(sceneName()))
                self.output_path_le.setReadOnly(1)
            else:
                self.output_path_le.setText(self.get_tmp_dir())
                self.output_path_le.setReadOnly(0)
        else:
            for le in self.stamp_asset_project_le, self.stamp_asset_user_le, self.stamp_asset_date_le, self.stamp_asset_version_le,\
                      self.stamp_asset_name_le, self.stamp_asset_step_le, self.stamp_asset_task_le, self.stamp_squens_project_le,\
                      self.stamp_squens_user_le, self.stamp_squens_date_le, self.stamp_squens_version_le, self.stamp_squens_name_le,\
                      self.stamp_squens_shot_le, self.stamp_squens_step_le, self.stamp_squens_task_le:
                le.setReadOnly(0)

        if not af_is_valid:
            self.render_tw.setCurrentIndex(1)
            self.render_tw.setTabEnabled(0, False)

        self.af_job_name_le.setText(self.default_job_name())
        if not self.add_light_preset_cbx.isChecked():
            self.light_setup_ai_grp.setDisabled(1)
            self.light_setup_ogl_grp.setDisabled(1)

    def update_ui(self):
        # self.rig_create_btn.setEnabled(not bool(self.camRig))
        # self.rig_remove_btn.setEnabled(bool(self.camRig))
        self.update_exists_cameras()

    def default_ui(self):
        if not self.ctx:
            if not shutgun_submit.is_valid:
                warning('Shotgun context not defined')
            # self.close()
            # return
        if self.ctx:
            if self.ctx['entity'] == 'shot':
                self.is_asset = False
                self.stamp_asset_wd.hide()
            else:
                self.is_asset = True
                self.stamp_sequence_wd.hide()
            self.stamp_mode_asset_rb.hide()
            self.stamp_mode_shot_rb.hide()

            self.stamp_asset_project_le.setText(self.ctx.get('project',emptyField))
            self.stamp_asset_project_le.setEnabled(0)
            self.stamp_asset_name_le.setText(self.ctx.get('name',emptyField))
            self.stamp_asset_step_le.setText(self.ctx.get('step',emptyField))
            self.stamp_asset_task_le.setText(self.ctx.get('task',emptyField))
            self.stamp_asset_user_le.setText(os.environ['USERNAME'])
            self.stamp_asset_version_le.setText('v01')


            self.stamp_squens_name_le.setText(self.ctx.get('sequence',emptyField))
            self.stamp_squens_task_le.setText(self.ctx.get('task',emptyField))
            self.stamp_squens_version_le.setText('v1')
            self.stamp_squens_step_le.setText(self.ctx.get('step',emptyField))
            self.stamp_squens_shot_le.setText(self.ctx.get('name',emptyField))
            self.stamp_squens_project_le.setText(self.ctx.get('project',emptyField))
            self.stamp_squens_user_le.setText(os.environ['USERNAME'])

        # else:
            # for i in range(self.asset_fields_grid_ly.count()):
            #     w = self.asset_fields_grid_ly.itemAt(i)

        self.set_current_date_to_field(self.stamp_squens_date_le)
        self.restore_var()
        if not self.ctx:
            self.stamp_asset_wd.setVisible(self.stamp_mode_asset_rb.isChecked())
            self.stamp_asset_wd.setEnabled(self.add_frame_stamp_cbx.isChecked())

            self.stamp_sequence_wd.setVisible(self.stamp_mode_shot_rb.isChecked())
            self.stamp_sequence_wd.setEnabled(self.add_frame_stamp_cbx.isChecked())


    def init_shaders_scene(self):
        # load shaders
        shaders = join(v.shaders_root, v.shaders_scene_name)
        if not os.path.exists(shaders):
            error('Shaders not found: %s' % shaders)
        r = self.ref_is_loaded(shaders)
        if not r:
            # r.load()
        # else:
            root = v.root_group()
            ref = createReference( shaders, namespace=(v.submitter_namespase) , returnNewNodes=1)
            nodes = [x for x in ref if hasattr(x,'getParent') and not x.getParent()]
            parent(nodes, root)

    def cleanup_scene(self):
        # self.remove_camera_rig()
        set = object_set.get_set(False)
        if set:
            delete(set)
        for mp in getPanel(type=ui.Panel('modelPanel')):
            modelEditor(mp, edit=1, dl="default", shadows=0, dtx=1)
        self.clear_layers()
        delete([x for x in ls() if x.hasAttr(shaders.special_attr_name)])
        v.root_group(remove=True)
        displayPref(displayGradient=self.viewport_gradient)
        displayRGBColor('background', *self.bg_color)
        self.unload_light_presets()
        self.unload_shareds()
        self.clear_session_id()
        self.close()
        self.deleteLater()

    def unload_light_presets(self):
        for r in listReferences():
            if r.namespace.startswith(v.submitter_namespase):
                if not r.path.basename() == v.shaders_scene_name:
                    r.remove()
        self.current_ref_scene = None

    def unload_shareds(self):
        for r in listReferences():
            if r.namespace.startswith(v.submitter_namespase):
                if r.path.basename() == v.shaders_scene_name:
                    r.remove()
        # QTimer.singleShot(300,lambda :v.root_group(remove=True))

    def define_current_scene(self):
        files = [x for x in os.listdir(v.scenes_root) if os.path.splitext(x)[-1] in ['.mb', '.ma']]
        for r in listReferences():
            if os.path.basename(r.path) in files:
                self.current_ref_scene = r.path
                if os.path.basename(r.path).startswith('ai'):
                    self.renderer_tab_tbw.setCurrentIndex(0)
                    ground = self.get_ground_plane(r)
                    if ground:
                        vis = ground.isVisible()
                        self.ai_use_ground_plane_cbx.setChecked(vis)
                        self.ai_ground_plane_texture_cbb.setEnabled(vis)
                elif os.path.basename(r.path).startswith('ogl'):
                    self.renderer_tab_tbw.setCurrentIndex(1)
                    ground = self.get_ground_plane(r)
                    if ground:
                        vis = ground.isVisible()
                        self.ogl_use_ground_plane_cbx.setChecked(vis)
                        self.ogl_ground_plane_texture_cbb.setEnabled(vis)

##################################### UPDATE

    def update_exists_cameras(self):
        t = self.render_camera_cbb.currentText()
        self.render_camera_cbb.blockSignals(1)
        self.render_camera_cbb.clear()
        for i, cam in enumerate(self.get_all_cameras()):
            self.render_camera_cbb.addItem(cam.name())
            self.render_camera_cbb.setItemData(i, cam.longName(), 32)
        if t:
            self.render_camera_cbb.setCurrentIndex(self.render_camera_cbb.findText(t))
        self.render_camera_cbb.blockSignals(0)

    def update_exists_ai_scenes(self):
        self.ai_scene_preset_cbb.clear()
        i = 0
        active = 0
        node = self.get_hdr_file_node()
        for f in os.listdir(v.hdr_root):
            if os.path.splitext(f)[-1] in ['.hdr', '.exr']:
                self.ai_scene_preset_cbb.addItem(os.path.splitext(f)[0])
                fullpath = join(v.hdr_root,f)
                if self.ref_is_loaded(fullpath):
                    self.current_ref_scene = fullpath
                self.ai_scene_preset_cbb.setItemData(i, fullpath, 32)
                if node:
                    if node.fileTextureName.get().replace('\\','/') == fullpath:
                        active = i
                i+=1
        self.ai_scene_preset_cbb.setCurrentIndex(active)
        self.ai_scene_preset_cbb.addItem('Custom...')

    def update_exists_textures(self):
        self.ai_ground_plane_texture_cbb.clear()
        self.ogl_ground_plane_texture_cbb.clear()
        i = 1
        active = 0

        texture = self.get_ground_plane_texture()
        if texture:
            texture = os.path.basename(texture.fileTextureName.get())

        self.ai_ground_plane_texture_cbb.addItem('None')
        self.ai_ground_plane_texture_cbb.setItemData(i, False, 32)
        self.ogl_ground_plane_texture_cbb.addItem('None')
        self.ogl_ground_plane_texture_cbb.setItemData(i, False, 32)
        for txd in os.listdir(v.txd_root):
            full = join(v.txd_root, txd)
            if os.path.isfile(full):
                if os.path.splitext(txd)[-1].lower() in ['.jpg', '.png', '.tga', '.exr', '.tiff', '.tif']:
                    self.ai_ground_plane_texture_cbb.addItem(txd)
                    self.ai_ground_plane_texture_cbb.setItemData(i, full, 32)

                    self.ogl_ground_plane_texture_cbb.addItem(txd)
                    self.ogl_ground_plane_texture_cbb.setItemData(i, full, 32)
                    if txd == texture:
                        active = i
                    i += 1
        self.ai_ground_plane_texture_cbb.addItem('Customize...')
        self.ai_ground_plane_texture_cbb.setItemData(i, '', 32)
        self.ogl_ground_plane_texture_cbb.addItem('Customize...')
        self.ogl_ground_plane_texture_cbb.setItemData(i, '', 32)

        self.ai_ground_plane_texture_cbb.setCurrentIndex(active)
        self.ogl_ground_plane_texture_cbb.setCurrentIndex(active)

    def update_exists_ogl_scenes(self):
        self.ogl_scene_preset_cbb.clear()
        i = 0
        active = 0
        for f in os.listdir(v.scenes_root):
            if os.path.splitext(f)[-1] in ['.ma', '.mb'] and f.startswith('ogl'):
                self.ogl_scene_preset_cbb.addItem(os.path.splitext(f)[0].title())
                fullpath = join(v.scenes_root,f)
                if self.ref_is_loaded(fullpath):
                    self.current_ref_scene = fullpath
                self.ogl_scene_preset_cbb.setItemData(i, fullpath, 32)
                if self.current_ref_scene == fullpath:
                    active = i
                i+=1
        self.ogl_scene_preset_cbb.setCurrentIndex(active)
        # self.ogl_scene_preset_cbb.addItem('Custom...')

    # def define_rig(self):
    #     rig = [x for x in ls(type='transform') if x.hasAttr(camera_rig.rig_attr_name+'_root')]
    #     if rig:
    #         self.camRig = rig[0]
    #         cams = [x for x in ls(cameras=True) if x.hasAttr(camera_rig.rig_attr_name)]
    #         if cams:
    #             for c in cams:
    #                 if c.attr(camera_rig.rig_attr_name).get() == 'orto':
    #                     self.ortoCam = c
    #                 elif c.attr(camera_rig.rig_attr_name).get() == 'persp':
    #                     self.perspCam = c
        # set = object_set.get_set(False)
        # if set:
        #     if set.members():
        #         self.box = camera_rig.get_bounding_box(set.members())
        # self.update_scalable_objects()

    def rebuild_rig(self):
        ln = nt.RenderLayer.currentLayer().name()
        if self.renderer_tab_tbw.currentIndex() == 0:
            s = self.ai_shaders.selectedItems()
            self.ai_shaders.rebuild_layers()
            if s:
                self.ai_shaders.setCurrentItem(s[0])

        else:
            s = self.ogl_shaders.selectedItems()
            self.ogl_shaders.rebuild_layers()
            if s:
                self.ogl_shaders.setCurrentItem(s[0])
        if objExists(ln):
            l = nt.RenderLayer.findLayerByName(ln)
            l.setCurrent()

    def renderer_tab_changed(self):
        use_preset = self.add_light_preset_cbx.isChecked()
        if not use_preset:
            camera_rig.reset_viewport()
            self.unload_light_presets()
        i = self.renderer_tab_tbw.currentIndex()
        if  i == TAB_AI:
            self.renderer = 'ai'
            if use_preset:
                self.load_arnold_scene()
            self.ai_shaders.update_objects_in_layers()
            self.ai_shaders.switch_selected_layer()
        elif i == TAB_OGL:
            self.renderer = 'ogl'
            if use_preset:
                self.load_ogl_scene()
            self.ogl_shaders.update_objects_in_layers()
            self.ogl_shaders.switch_selected_layer()
        # self.afanasy_grp.setEnabled(i==0)
        self.init_shaders_scene()
        self.update_scalable_objects()
        self.update_info()

    def clear_layers(self, tp=''):
        #todo: replace to manager function to delete
        for layer in ls(type='renderLayer'):
            if layer.name().startswith(v.render_layer_prefix+tp):
                mel.renderLayerEditorDeleteLayer('RenderLayerTab', layer)
##########################################  VARIABLES

    def save_var(self):
        c = config.Config()
        data = c.get()
        newdata = dict(
            ogl_scene_preset_cbb=self.ogl_scene_preset_cbb.currentIndex(),
            ogl_use_ground_plane_cbx=self.ogl_use_ground_plane_cbx.isChecked(),
            ogl_ground_plane_texture_cbb=self.ogl_ground_plane_texture_cbb.currentIndex(),
            ai_render_background_cbx=self.ai_render_background_cbx.isChecked(),
            ai_scene_preset_cbb=self.ai_scene_preset_cbb.currentIndex(),
            ai_use_ground_plane_cbx=self.ai_use_ground_plane_cbx.isChecked(),
            ai_ground_plane_texture_cbb=self.ai_ground_plane_texture_cbb.currentIndex(),

            persp_res_cbb=self.persp_res_cbb.currentIndex(),
            render_as_video_rb=self.render_as_video_rb.isChecked(),
            join_videos_cbx=self.join_videos_cbx.isChecked(),
            join_images_cbx=self.join_images_cbx.isChecked(),
            add_frame_stamp_cbx=self.add_frame_stamp_cbx.isChecked(),

            af_paused_cbx=self.af_paused_cbx.isChecked(),
            af_host_mask_le=self.af_host_mask_le.text(),
            af_job_depend_mask_le=self.af_job_depend_mask_le.text(),
            post_cmd_cbb=self.post_cmd_cbb.currentIndex(),
            local_paused_cbx=self.local_paused_cbx.isChecked(),

            font_size_sbx=self.stamp_opt_window.font_size_sbx.value(),
            opacity_sld=self.stamp_opt_window.opacity_sld.value(),
            backdrop_cbx=self.stamp_opt_window.backdrop_cbx.isChecked()
        )
        data.update(newdata)
        if not self.ctx:
            standalone_data = dict(
                output_path_le=self.output_path_le.text(),
                stamp_mode_shot_rb=self.stamp_mode_shot_rb.isChecked(),
                stamp_asset_project_le=self.stamp_asset_project_le.text(),
                stamp_asset_user_le=self.stamp_asset_user_le.text(),
                # stamp_asset_date_le=self.stamp_asset_date_le.text(),
                stamp_asset_version_le=self.stamp_asset_version_le.text(),
                stamp_asset_step_le=self.stamp_asset_step_le.text(),
                stamp_asset_task_le=self.stamp_asset_task_le.text(),
                stamp_asset_name_le=self.stamp_asset_name_le.text(),
                stamp_asset_frame_cbx=self.stamp_asset_frame_cbx.isChecked(),
                stamp_squens_name_le=self.stamp_squens_name_le.text(),
                stamp_squens_shot_le=self.stamp_squens_shot_le.text(),
            )
            data.update(standalone_data)
        c = config.Config()
        c.save(data)

    def restore_var(self):
        c = config.Config()
        data = c.get()
        self.ogl_scene_preset_cbb.setCurrentIndex(data.get('ogl_scene_preset_cbb', 0) )
        self.ogl_use_ground_plane_cbx.setChecked(data.get('ogl_use_ground_plane_cbx', True) )
        self.ogl_ground_plane_texture_cbb.setCurrentIndex(data.get('ogl_ground_plane_texture_cbb', 0) )
        self.ai_render_background_cbx.setChecked(data.get('ai_render_background_cbx', True) )
        self.ai_scene_preset_cbb.setCurrentIndex(data.get('ai_scene_preset_cbb', 0) )
        self.ai_use_ground_plane_cbx.setChecked(data.get('ai_use_ground_plane_cbx', True) )
        self.ai_ground_plane_texture_cbb.setCurrentIndex(data.get('ai_ground_plane_texture_cbb', 0) )
        self.persp_res_cbb.setCurrentIndex(data.get('persp_res_cbb', 2) )
        if data.get('render_as_video_rb', True):
            self.render_as_video_rb.setChecked(True)
        else:
            self.render_as_images_rb.setChecked(True)
        self.join_videos_cbx.setChecked(data.get('join_videos_cbx', True) )
        self.join_images_cbx.setChecked(data.get('join_images_cbx', True) )
        self.add_frame_stamp_cbx.setChecked(data.get('add_frame_stamp_cbx', True) )
        self.local_paused_cbx.setChecked(data.get('local_paused_cbx', True) )
        self.post_cmd_cbb.setCurrentIndex(data.get('post_cmd_cbb', 0) )

        self.stamp_opt_window.font_size_sbx.setValue(data.get('font_size_sbx', 14) ),
        self.stamp_opt_window.opacity_sld.setValue(data.get('opacity_sld', 70) ),
        self.stamp_opt_window.backdrop_cbx.setChecked(data.get('backdrop_cbx', True) )

        if not self.ctx:
            self.output_path_le.setText(data.get('output_path_le', '') )
            if data.get('stamp_mode_shot_rb', True):
                self.stamp_mode_shot_rb.setChecked(True)
            else:
                self.stamp_mode_asset_rb.setChecked(True)
            self.stamp_asset_project_le.setText(data.get('stamp_asset_project_le', '') )
            self.stamp_asset_user_le.setText(data.get('stamp_asset_user_le', '') )
            # self.stamp_asset_date_le.setText(data.get('stamp_asset_date_le', '') )
            self.stamp_asset_version_le.setText(data.get('stamp_asset_version_le', '') )
            self.stamp_asset_step_le.setText(data.get('stamp_asset_step_le', '') )
            self.stamp_asset_task_le.setText(data.get('stamp_asset_task_le', '') )
            self.stamp_asset_name_le.setText(data.get('stamp_asset_name_le', '') )
            self.stamp_asset_frame_cbx.setChecked(data.get('stamp_asset_frame_cbx', True) )
            self.stamp_squens_name_le.setText(data.get('stamp_squens_name_le', '') )
            self.stamp_squens_shot_le.setText(data.get('stamp_squens_shot_le', '') )
        self.af_paused_cbx.setChecked(data.get('af_paused_cbx', False) )
        self.af_host_mask_le.setText(data.get('af_host_mask_le', '') )
        self.af_job_depend_mask_le.setText(data.get('af_job_depend_mask_le', '') )

        ffmpeg_path = data.get('ffmpeg_path')
        if not ffmpeg_path:
            ffmpeg = os.path.join(os.path.dirname(__file__),'tools', 'bin', 'ffmpeg.exe').replace('\\','/')
            if os.path.exists(ffmpeg):
                data['ffmpeg_path'] = ffmpeg
            else:
                QMessageBox.critical(self, 'ffmpeg.exe not found', 'File ffmpeg.exe not found\nPlease select "ffmpeg.exe" file in you computer')
                res = QFileDialog.getSaveFileName(self, 'Select ffmpeg.exe file', "",
                                        "FFMPEG (ffmpeg.exe)")
                if not res:
                    self.submit_btn.setEnabled(0)
                else:
                    data['ffmpeg_path'] = res[0].replace('\\','/')
            c.save(data)


################################################ UI ELEMENTS

    def out_path_custom_menu(self):
        m = QMenu()
        m.addAction(QAction('Scene Folder', self, triggered=lambda :self.output_path_le.setText(sceneName().dirname())))
        m.addAction(QAction('Project Root', self, triggered=lambda :self.output_path_le.setText(system.Workspace.getPath())))
        brAct = QAction('Browse...', self)
        @brAct.triggered.connect
        def browse_out_folder():
            f = self.output_path_le.text()
            f = f if os.path.exists(f) else ''
            path = QFileDialog.getExistingDirectory(self, 'Chose output folder', f)
            if path:
                self.output_path_le.setText(path)
        m.addAction(brAct)
        c = config.Config()
        data = c.get()
        his = data.get('out_folder_history',[])
        if his:
            m.addSeparator()
            for h in his:
                m.addAction(QAction(h, self, triggered=lambda p=h:self.output_path_le.setText(p)))
            m.addSeparator()
            m.addAction(QAction('Clear History', self, triggered=lambda :config.Config().set('out_folder_history', [])))
        m.exec_(QCursor.pos())

    def date_field_custom_menu(self):
        m = QMenu()
        m.addAction(QAction('Set Current Time', self, triggered=lambda :self.set_current_date_to_field(self.sender())))
        m.exec_(QCursor.pos())

    def set_current_date_to_field(self, field):
        # field = field or self.sender()
        danemask = 'dd.MM.yyyy h:m'
        field.setText(QDateTime.currentDateTime().toString(danemask))

################################################ CAMERAS

    def create_camera_rig_OLD(self):
        obj = object_set.content()
        if not obj:
            warning('Add objects to set before')
        self.ortoCam, self.perspCam, self.camRig  = camera_rig.create_cameras(obj, turntableLen=self.turn_frames_sbx.value(),
                                                                                   persp=self.turn_cam_cbx.isChecked(),
                                                                                   orto=self.orto_cams_cbx.isChecked())
        # self.box = camera_rig.get_bounding_box(self.shaded_objects())
        select(cl=1)
        self.update_ui()

        cam = self.perspCam or self.ortoCam

        if cam:
            self.render_camera_cbb.setCurrentIndex(max([self.render_camera_cbb.findText('turntable_camera1'), 0]))
            lookThru(cam)
            self.range_end_sbx.setValue(self.turn_frames_sbx.value())

    def create_new_camera_rig(self):
        reload(camera_rig)
        objs = object_set.content()
        if not objs:
            warning('No objects in Set')
            return
        if camera_rig.rigs:
            menu = QMenu()
            for rig in camera_rig.rigs:
                a = QAction(rig.title, self)
                a.setData(rig)
                menu.addAction(a)
            a = menu.exec_(QCursor.pos())
            if a:
                rig = a.data()
                cam, start, end = rig.create(objs)
                select(cl=1)
                self.update_ui()
                self.render_camera_cbb.setCurrentIndex(max([self.render_camera_cbb.findText(cam.name()), 0]))
                lookThru(cam)
                env.setPlaybackTimes([start,start,end,end])

    def update_ui_from_camera(self):
        cam = self.render_camera_cbb.itemData(self.render_camera_cbb.currentIndex(), 32)
        if cam:
            if objExists(cam):
                cam = PyNode(cam)
                lookThru(cam)
                if cam.hasAttr(camera_rig.BaseRig.cam_attr_name):
                    d = cam.attr(camera_rig.BaseRig.cam_attr_name).get()
                    try:
                        d = json.loads(d)
                        self.range_start_sbx.setValue(d['range'][0])
                        self.range_end_sbx.setValue(d['range'][1])
                        env.setPlaybackTimes([d['range'][0],d['range'][0],d['range'][1],d['range'][1]])
                    except:
                        cam.attr(camera_rig.BaseRig.cam_attr_name).set(json.dumps([]))

    def get_custom_cameras(self):
        cam = self.render_camera_cbb.currentText()
        if objExists(cam):
            return [PyNode(cam), self.custom_start_spx.value(), self.custom_end_spx.value()]
        return []

    def get_all_cameras(self):
        cams = [x.getParent() for x in ls(cameras=1) if not x.getParent().name() in ['front', 'back', 'side', 'right','top','bottom']]
        return cams #[x for x in cams if not x.hasAttr(camera_rig.rig_attr_name)]

    def get_camera_ranges(self):
        ranges = []
        if self.cameras_tab.currentIndex() == 0:
            start = self.range_start_sbx.value()
            end = self.range_end_sbx.value()
            if start >= end:
                PopupError('Wrong frame range %s-%s' % (start, end))
                return
            camname = self.render_camera_cbb.currentText()
            if not objExists(camname):
                PopupError('Wrong camera %s' % camname)
                return
            ranges = [{"camera":camname,
                        "start":start,
                          "end":end,
                         "step":1,
                         "orto": int(PyNode(camname).orthographic.get())}]
        return ranges

    def get_resolution(self):
        return v.res_repsp[self.persp_res_cbb.currentIndex()]

############################################# SCENE RIG

    def get_ground_plane(self, ref=None):
        if not ref:
            if self.current_ref_scene:
                ref = self.ref_is_loaded(self.current_ref_scene)
                if not ref:
                    return
        objs = [x for x in ref.nodes() if x.hasAttr(v.submitter_rig_attribute_name)]
        for o in objs:
            if o.attr(v.submitter_rig_attribute_name).get() == 'ground':
                return o

    def update_ground(self,ref=None):
        ground = self.get_ground_plane(ref)
        if ground:
            show = True
            if self.renderer_tab_tbw.currentIndex() == 0:
                show = self.ai_use_ground_plane_cbx.isChecked()
            elif self.renderer_tab_tbw.currentIndex() == 1:
                show = self.ogl_use_ground_plane_cbx.isChecked()
            if not show:
                self.show_hide_ground_plane(False)
            else:
                sh = self.ground_shader()
                if sh:
                    sets(sh.shadingGroups()[0], forceElement=ground)
                # self.move_ground(ground, camera_rig.get_bounding_box(self.shaded_objects()) or camera_rig.get_bounding_box())
        else:
            print 'Ground not found'

    def show_hide_ground_plane(self, val=None):
        ground = self.get_ground_plane()
        if ground:
            if val is None:
                val = self.sender().isChecked()
            if val:
                # self.move_ground(ground, self.box or camera_rig.get_bounding_box())
                ground.show()
                self.update_ground()
            else:
                ground.hide()

    def ground_shader(self):
        shName = self.renderer + '_ground_shader'
        sh = [x for x in ls(materials=1) if x.stripNamespace() == shName]
        if sh:
            return sh[0]

    def get_ground_plane_texture(self):
        sh = self.ground_shader()
        if sh:
            file = sh.color.inputs()
            if file:
                file = file[0]
                if file.type() == 'file':
                    return file
                else:

                    return find_file(file)

    def update_scalable_objects(self):
        if not self.add_light_preset_cbx.isChecked():
            return
        # src = selected()[0]
        # addAttr(src,ln="submitterScaleFactor", at='double', dv=0)
        bound = camera_rig.BaseRig.get_bounding_box()
        if not bound:
            scale = 0
        else:
            scale = max(bound.width(), bound.depth())
        scale_nodes = []
        ref = self.ref_is_loaded(self.current_ref_scene)
        if ref:
            scale_nodes = [x for x in ref.nodes() if x.hasAttr(v.submitter_scale_attribute_name)]
        if not scale_nodes:
            return
        max_d = 0
        for obj in scale_nodes:
            if bound:
                obj.tx.set(bound.center()[0])
                obj.ty.set(bound.min()[1])
                obj.tz.set(bound.center()[2])
            s = obj.attr(v.submitter_scale_attribute_name).get()
            obj.s.set(scale*s,scale*s,scale*s)
            bb = obj.getBoundingBox(space='world')
            max_d = max([max_d, max(bb.width(), bb.depth())])
        if max_d and max_d > 3:
            for c in ls(cameras=1):
                c.farClipPlane.set(max(0.01,max_d*0.7))
                c.nearClipPlane.set(max(0.01,max_d*0.001))

    def set_ground_texture(self, i=None, path=None):
        if path is None:
            path = self.sender().itemData(i, 32)
        shName = self.renderer + '_ground_shader'
        sh = self.ground_shader()
        if path == '':
            select(sh)
            return
        # ground = self.get_ground_plane()
        if sh:
            if not path:
                sh.color.disconnect()
                sh.color.set(0.7, 0.7, 0.7)
                print 'disconnect', sh
            else:
                inp = sh.color.inputs()
                if not inp:
                    txdfilenode = PyNode(sh.namespace()+'ground_texture_file')
                    txdfilenode.outColor >> sh.color
                else:
                    txdfilenode = inp[0]
                    if not txdfilenode.type() == 'file':
                        txdfilenode = find_file(txdfilenode)
                if txdfilenode:
                    txdfilenode.fileTextureName.set(path)
                    # sets(sh.shadingGroups()[0], forceElement=ground)
                    # correct texture size
                    ground = self.get_ground_plane()
                    if not ground:
                        return
                    pls = txdfilenode.uvCoord.inputs()
                    if pls:
                        pls = pls[0]
                    else:
                        return
                    grSize = ground.getBoundingBox(space='world').width()
                    box = camera_rig.BaseRig.get_bounding_box()
                    boxSize = max(box.width(), box.depth())
                    pls.offsetV.set(0.5)
                    pls.offsetU.set(0.5)
                    x, y = txdfilenode.outSize.get()
                    pls.repeatU.set((grSize/boxSize))
                    pls.repeatV.set((grSize/boxSize)*(x/y))

        else:
            print 'shader not found', shName

        # node = self.get_ground_plane_texture()

########################################## AI ACTIONS

    def get_environment(self, ref=None):
        if not ref:
            if self.current_ref_scene:
                ref = self.ref_is_loaded(self.current_ref_scene)
                if not ref:
                    return
        objs = [x for x in ref.nodes() if x.hasAttr(v.submitter_rig_attribute_name)]
        for o in objs:
            if o.attr(v.submitter_rig_attribute_name).get() == 'env':
                return o

    def update_hdr(self, i=None):
        if i is None:
            i = self.ai_scene_preset_cbb.currentIndex()
        hdr = self.ai_scene_preset_cbb.itemData(i, 32)
        node = self.get_hdr_file_node()
        if node:
            if not hdr:
                select(node)
            else:
                node.fileTextureName.set(hdr)

    def get_hdr_file_node(self):
        ref = self.ref_is_loaded(self.current_ref_scene)
        if ref:
            filenodes = [x for x in ref.nodes() if x.stripNamespace() == 'hdri_file']
            if filenodes:
                return filenodes[0]

    def connect_aiSky(self):
        ref = self.ref_is_loaded(self.current_ref_scene)
        if not ref:
            return
        sky = ([x for x in ref.nodes() if x.type() == 'aiSky'] or [None])[0]
        if sky:
            if self.ai_render_background_cbx.isChecked():
                sky.message >> PyNode('defaultArnoldRenderOptions').background
            else:
                PyNode('defaultArnoldRenderOptions').background.disconnect()


######################################### LOAD

    def load_arnold_scene(self):
        # REMOVE OGL LAYERS
        self.clear_layers('ogl')
        scene = join(v.scenes_root, 'ai_scene.ma')
        script = join(v.scenes_root, 'ai.py')
        if self.current_ref_scene == scene:
            execfile(script)
            # ref = self.ref_is_loaded(scene)
            # if ref:
            #     self.update_ground(ref)
            return
        if self.ref_is_loaded(scene):
            self.current_ref_scene = scene
            execfile(script)
            return
        if self.current_ref_scene:
            ref = self.ref_is_loaded(self.current_ref_scene)
            if ref:
                ref.remove()
        if os.path.exists(scene):
            # load ref
            ref = createReference( scene, namespace=(v.submitter_namespase) )
            roots = [x for x in ref.nodes() if hasattr(x, 'getParent') and not x.getParent()]
            if roots:
                root_gtp = v.root_group()
                for r in roots:
                    r.setParent(root_gtp)
            execfile(script)
            self.current_ref_scene = scene

            # self.update_ground(ref)
            self.connect_aiSky()
            self.update_hdr()
        else:
            error('Reference scene not found!')
        self.update_scalable_objects()
        self.ai_shaders.check_list()
        self.update_ground()
        select(cl=1)

    def load_ogl_scene(self):
        # REMOVE AI LAYERS
        self.clear_layers('ai')
        it = self.ogl_scene_preset_cbb.currentIndex()
        scene = self.ogl_scene_preset_cbb.itemData(it, 32)
        if scene:
            # scene = join(v.scenes_root, 'ogl_outdor.ma')
            script = join(v.scenes_root, 'ogl.py')
            if self.current_ref_scene == scene:
                execfile(script)
                return
            if self.current_ref_scene:
                ref = self.ref_is_loaded(self.current_ref_scene)
                if ref:
                    ref.remove()
            if os.path.exists(scene):
                # load ref
                ref = createReference( scene, namespace=(v.submitter_namespase) )
                roots = [x for x in ref.nodes() if hasattr(x, 'getParent') and not x.getParent()]
                if roots:
                    root_gtp = v.root_group()
                    for r in roots:
                        r.setParent(root_gtp)
                execfile(script)
                self.current_ref_scene = scene
        self.ogl_shaders.check_list()
        self.update_scalable_objects()
        self.update_ground()
        select(cl=1)

    def ref_is_loaded(self,path):
        for r in listReferences():
            if r.path == path:
                return r

    ################################### OBJECTS AND SET

    def add_objects_to_set(self, objects=None):
        objects = objects or selected()
        object_set.add_to_set(objects)
        # self.renderer_tab_changed()
        ref = self.ref_is_loaded(self.current_ref_scene)
        if ref:
            self.update_ground(ref)
            self.update_scalable_objects()
        self.rebuild_rig()

    def remove_objects_from_set(self, objects=None):
        objects = objects or selected()
        object_set.remove_from_set(objects)
        self.update_scalable_objects()
        self.rebuild_rig()

    def select_objects_in_set(self):
        select(object_set.content())

    def delete_object_set(self):
        cont = object_set.content()
        if cont:
            self.remove_objects_from_set(cont)
        s = object_set.get_set(False)
        if s:
            delete(s)
        self.rebuild_rig()

    def shaded_objects(self):
        return [x for x in self.render_objects() if not x in self.studio_objects()]

    def render_objects(self):
        # if self.isolate_objects_cbx.isChecked():
        objects = object_set.content() + self.studio_objects()
        return objects
        # else:
        #     return [x for x in ls(transforms=1) if not x.hasAttr(shaders.special_attr_name)]

    def studio_objects(self):
        if self.current_ref_scene:
            r = self.ref_is_loaded(self.current_ref_scene)
            if r:
                nodes = [x for x in r.nodes() if hasattr(x, 'getShape') and x.getShape()]
                return nodes
        return []

    def create_session_id(self):
        try:
            n = PyNode(v.session_id_node_name)
            return n.attr(v.session_id_attrib).get()
        except:
            n = createNode('network', name=v.session_id_node_name)
            addAttr(n, ln=v.session_id_attrib, dt='string')
            id = generate_id()
            n.attr(v.session_id_attrib).set(id)
            return id

    def clear_session_id(self):
        try:
            n = PyNode(v.session_id_node_name)
            delete(n)
        except:
            pass
        self.global_output = None
        self.group_block = 0
        self.blocks.update_from_folder()
        self.session_id = self.create_session_id()

    def clear_blocks(self):
        folder = self.global_output_folder(False)
        if folder and os.path.exists(folder):
            shutil.rmtree(folder)
        self.clear_session_id()
        self.blocks.update_from_folder()

############################################### SUBMIT 2 ####################################

    def global_output_folder(self, create=True):
        if self.global_output:
            if not os.path.exists(self.global_output):
                os.makedirs(self.global_output)
            return self.global_output
        # create new
        tmp = self.get_tmp_dir()
        foldername = 'previewer_render_%s' % self.session_id
        self.global_output = join(tmp, foldername)
        if create:
            if not os.path.exists(self.global_output):
                os.makedirs(self.global_output)
        return self.global_output

    def export_blocks(self):

        # check scene
        if not self.check_scene():
            return
        if not self.check_settings():
            return
        # get default data
        source_datafile = os.path.join(os.path.dirname(__file__), 'tools', 'datafile_example.json')
        if not os.path.exists(source_datafile):
            error('Source Data File not found')
            return
        default_data = json.load(open(source_datafile))
        default_data['resolution'] = self.get_resolution()
        ranges = self.get_camera_ranges()
        if not ranges:
            PopupError('Empty frame range')
            return
        default_data['ranges'] = ranges
        default_data['font'] = None
        # get layers
        layers = [x for x in ls(type='renderLayer') if x.hasAttr(shaders.layerSubmitterAttr) and x.renderable.get()]
        if not layers:
            warning('Layers not created')
            return
        tmpDir = self.global_output_folder()
        default_data['stamp'] = self.get_stamp_data() if self.add_frame_stamp_cbx.isChecked() else None
        default_data['mayadir'] = self.get_maya_locaion()
        outdir = self.result_output_folder()
        default_data['outputdir'] = outdir
        # preview image
        # skipped
        # format file
        if self.render_as_video_rb.isChecked():
            default_data['ismove'] = True
            if self.join_videos_cbx.isChecked():
                default_data['join_outputs'] = True
            else:
                default_data['join_outputs'] = False
        else:
            default_data['ismove'] = False
            if self.join_images_cbx.isChecked():
                default_data['join_outputs'] = True
            else:
                default_data['join_outputs'] = False
        # file count
        if self.render_as_video_rb.isChecked():
            if self.join_videos_cbx.isChecked():
                filecount = 1
            else:
                filecount = len(layers)
        else:
            if self.join_images_cbx.isChecked():
                filecount = len(layers)
            else:
                filecount = len(layers) * sum([x['end']-x['start']+1 for x in ranges])
        default_data['group'] = self.group_block

        if pluginInfo('mtoa',q =1, l=1):
            path = pluginInfo('mtoa',q =1, path=1)
            mtoa_root = os.path.dirname(os.path.dirname(path))
            default_data['mtoa_path'] = mtoa_root

        self.group_block += 1
        for layer in layers: # for each layer
            layer.setCurrent()
            data = default_data.copy()
            if displayPref(q=1,displayGradient=1):
                data['viewport_backdrop'] = False
            else:
                data['viewport_backdrop'] = displayRGBColor('background', query=1)
            layer_id = generate_id()
            data['id'] = layer_id
            tmpname = 'afrender_'+layer_id
            temp = os.path.join(tmpDir, tmpname).replace('\\','/')
            if not os.path.exists(temp):
                os.makedirs(temp)
            data['tmpdir'] = temp
            #todo: add script node to setup viewport for OGL
            data['mayascene'] = self.save_scene_to_tmp(temp, layer, layer_id)
            if layer.hasAttr(shaders.layerNameAttr):
                layername = layer.attr(shaders.layerNameAttr).get().replace(' ', '_')
            else:
                layername = 'Noname'
            data['layer'] = layer.name()
            # json filename
            filename = '_'.join([os.path.basename(data['mayascene']).split('.')[0], layername])
            data['outfilename'] = filename
            data['movfile'] = os.path.join(os.path.dirname(data['mayascene']), filename).replace('\\','/') + '.mp4'
            if self.renderer_tab_tbw.currentIndex() == TAB_AI:
                data['engine'] = 'ai'
                data['ai_data'] = None
            elif self.renderer_tab_tbw.currentIndex() == TAB_OGL:
                if layer.hasAttr(shaders.oglEngineAttrName):
                    data['engine'] = layer.attr(shaders.oglEngineAttrName).get()
                else:
                    data['engine'] = shaders.LayerManager.ogl_engine
                ogl_data = dict(
                    ao_enable=PyNode('hardwareRenderingGlobals').ssaoEnable.get()
                    # shadows
                    # textures
                    # AA
                )
                data['ogl_data'] = ogl_data
            # save data file
            datafile = os.path.join(temp, os.path.splitext(os.path.basename(data['mayascene']))[0] + '.json').replace('\\','/')
            data = {k:v for k, v in data.items() if k}
            json.dump(data, open(datafile, 'w'), indent=4)
        self.blocks.update_from_folder(self.global_output)

    def submit_blocks(self):
        files = self.blocks.get_data_files()
        if not files:
            PopupError('No blocks to submit')
            warning('No blocks to submit')
            return
        # self.result_output_folder()
        datafiles = []
        for f in files:
            datafiles.append(dict(
                path=f,
                data=json.load(open(f))
            ))
        if self.render_tw.currentIndex() == 0:
            self.send_to_afanasy(datafiles, self.result_output_folder())
        elif self.render_tw.currentIndex() == 1:
            self.submit_local(datafiles, self.result_output_folder())
            c = config.Config()
            path = self.output_path_le.text()
            data = c.get()
            if 'out_folder_history' in data:
                if path in data['out_folder_history']:
                    data['out_folder_history'].remove(path)
                data['out_folder_history'].append(path)
            else:
                data['out_folder_history'] = [path]
            c.save(data)


    def check_scene(self):
        delete(ls(type='unknown'))
        return True

    def check_settings(self):
        out = self.result_output_folder()
        if not out:
            warning('Output path not set')
            return False
        # if not os.path.exists(out):
        #     confirmBox('Title', 'Question')
        return True

    def confirm_dialog(self):
        pass

############################################### SUBMIT ######################################

    def submit_old(self):
        if not sceneName():
            PopupError('Save scene before continue')
            return

        # check context
        if shutgun_submit.is_valid:
            current_context = shutgun_submit.context()
            if not current_context == self.ctx:
                PopupError('Context is changed! Restart Submitter')
                return
        delete(ls(type='unknown'))
        source_datafile = os.path.join(os.path.dirname(__file__), 'tools', 'datafile_example.json')
        if not os.path.exists(source_datafile):
            error('Source Data File not found')
            return
        default_data = json.load(open(source_datafile))

        ##################### confirm dialog
        enable_submit = True
        default_data['context'] = self.ctx

        data_files = []
        # collect cameras and ranges
        ranges = self.get_camera_ranges()
        if not ranges:
            PopupError('Empty frame range')
            return
        # print ranges
        # return
        # default_data['resolution'] = v.res_default # [int(x.strip()) for x in self.persp_res_cbb.currentText().split('x')]
        default_data['resolution'] = self.get_resolution() # [int(x.strip()) for x in self.persp_res_cbb.currentText().split('x')]
        default_data['ranges'] = ranges
        default_data['font'] = None
        # collect layers
        layers = [x for x in ls(type='renderLayer') if x.hasAttr(shaders.layerSubmitterAttr) and x.renderable.get()]
        tmpDir = self.get_tmp_dir()
        if self.add_frame_stamp_cbx.isChecked():
            default_data['stamp'] = self.get_stamp_data()
        else:
            default_data['stamp'] = None
        default_data['mayadir'] = self.get_maya_locaion()
        outdir = self.result_output_folder()
        print 'OUTPUT', outdir
        default_data['outputdir'] = outdir
        ########################################################## CONFIRM DIALOG
        # preview image
        path = self.render_current_frame_ogl()
        if self.add_frame_stamp_cbx.isChecked():
            stampdata = self.get_stamp_data()
            pix = preview_widget.PreviewWidget.get_stamped_pixmap(path, stampdata, int(currentTime()))
            preview_path = path#tempfile.gettempdir() + '/quickpreviewfile_%s.png' % str(random.randrange(100000,999999))
            if os.path.exists(preview_path):
                os.remove(preview_path)
            pix.save(preview_path, 'PNG')
        else:
            preview_path = path
        # afanasy data
        if self.use_afanasy_cbx.isChecked():
            servdata = af_util.get_server_info()
            af_data = ['Use: YES',
                       'Server: %s' % servdata['server'],
                       'Paused: %s' % ('YES' if self.af_paused_cbx.isChecked() else 'NO')]
        else:
            af_data = ['Use: NO']

        # output data
        out_data = [
            'Output file: %s' % 'MP4' if self.render_as_video_rb.isChecked() else 'PNG',
            'Resolution: %s' % self.persp_res_cbb.currentText()
        ]
        # format file
        if self.render_as_video_rb.isChecked():
            default_data['ismove'] = True
            if self.join_videos_cbx.isChecked():
                default_data['join_outputs'] = True
            else:
                default_data['join_outputs'] = False
            out_data.append('Join videos: %s' % ('YES' if self.join_videos_cbx.isChecked() else 'NO'))
        else:
            default_data['ismove'] = False
            if self.join_images_cbx.isChecked():
                default_data['join_outputs'] = True
            else:
                default_data['join_outputs'] = False
            out_data.append('Join Images: %s' % ('YES' if self.join_images_cbx.isChecked() else 'NO'))
        # shotgun data
        shotgun_data = []
        if self.render_as_video_rb.isChecked():
            if self.join_videos_cbx.isChecked():
                filecount = 1
            else:
                filecount = len(layers)
        else:
            if self.join_images_cbx.isChecked():
                filecount = len(layers)
            else:
                filecount = len(layers) * sum([x['end']-x['start']+1 for x in ranges])
        if not layers:
            enable_submit = False
        if filecount == 0 or filecount > conf['max_files_to_publish']:
            enable_submit = False
        shotgun_data.append('Files to publish: %s' % (filecount if (filecount < conf['max_files_to_publish'] and filecount != 0) else '<span style="color:red;"><b>%s</b></span>' % filecount))
        shotgun_data.append('Comment: %s' % ('<br>'+self.comment_le.toPlainText().replace('\n', '<br>') if self.comment_le.toPlainText() else '-'))
        shotgun_data.append('Publish path: %s' % outdir)
        # generate data
        data = {
            '$PREVIEW$':    preview_path,
            '$PATHS$':      ['Scene: '+sceneName(), 'Temp : '+tmpDir, 'Output : ' + outdir],
            '$CAMS$':       ['{name} ({st}-{en}) {orto}'.format(name=x['camera'],
                                                                st=x['start'],
                                                                en=x['end'],
                                                                orto='<b>  ORTHOGRAPHIC</b>' if x['orto'] else '') for x in ranges],
            '$LAYERS$':     [x.name() for x in layers] if layers else ['<span style="color:red;"><b>No Layers Created</b></span>'],
            '$ENGINE$':     'OpenGL' if self.renderer_tab_tbw.currentIndex() == 1 else 'Arnold',
            '$MAYAVER$':    about(version=1),
            '$AFANASY$':    af_data,
            '$OUTFILES$':   out_data,
            '$SHOTGUN$':    shotgun_data
        }

        if not os.path.exists(outdir):
            try:
                os.makedirs(outdir)
            except:
                PopupError('Error create output folder\n'+outdir)
                return

        dial = confirm_gialog.ConfirmDialog(data, self)

        # check submit available
        dial.continue_btn.setEnabled(enable_submit)
        if not dial.exec_():
            try:
                os.remove(preview_path)
            except:
                pass
            try:
                shutil.rmtree(outdir)
            except:
                pass
            return

        try:
            os.remove(preview_path)
        except:
            pass


        # test_out_folder = self.result_output_folder()
        # if not outdir == test_out_folder:
        #     default_data['outputdir'] = test_out_folder
        ######################################################################### CONTINUE

        for layer in layers: # for each layer
            layer.setCurrent()
            data = default_data.copy()
            if displayPref(q=1,displayGradient=1):
                data['viewport_backdrop'] = False
            else:
                data['viewport_backdrop'] = displayRGBColor('background', query=1)
            id = str(random.randrange(100000,999999))
            data['id'] = id
            tmpname = 'afrender_'+id
            temp = os.path.join(tmpDir, tmpname).replace('\\','/')
            if not os.path.exists(temp):
                os.makedirs(temp)
            data['tmpdir'] = temp

            # save scene
            data['mayascene'] = self.save_scene_to_tmp(temp, layer, id)
            # layer
            if layer.hasAttr(shaders.layerNameAttr):
                layername = layer.attr(shaders.layerNameAttr).get().replace(' ', '_')
            else:
                layername = 'Noname'
            data['layer'] = layer.name()
            # filename
            filename = '_'.join([os.path.basename(data['mayascene']).split('.')[0], layername])
            data['outfilename'] = filename
            data['movfile'] = os.path.join(os.path.dirname(data['mayascene']), filename).replace('\\','/') + '.mp4'
            if self.renderer_tab_tbw.currentIndex() == 0:
                data['engine'] = 'ai'
            else:
                if layer.hasAttr(shaders.oglEngineAttrName):
                    data['engine'] = layer.attr(shaders.oglEngineAttrName).get()
                else:
                    data['engine'] = shaders.LayerManager.ogl_engine

            # save data file
            datafile = os.path.join(temp, os.path.splitext(os.path.basename(data['mayascene']))[0] + '.json').replace('\\','/')
            data = {k:v for k, v in data.items() if k}
            json.dump(data, open(datafile, 'w'), indent=4)
            data_files.append({'data': data, 'path':datafile})
        # print [x['path'] for x in data_files]
        self.send_to_afanasy(data_files, outdir)

    def get_output_dir(self):
        if self.ctx:
            name = sceneName().basename() or 'untitled'
            dir = join(shutgun_submit.review_folder(sceneName()), name)
            if not os.path.exists(dir):
                os.makedirs(dir)
            return dir
        else:
            return

    def get_tmp_dir(self):
        f = os.getenv('AMG_TEMP') or 'c:/temp'
        if not os.path.exists(f):
            os.makedirs(f)
        return f

    def get_maya_locaion(self):
        return mayautils.getMayaLocation().replace('\\','/')

    def save_scene_to_tmp(self, folder, layer, id):
        if not layer:
            PopupError('Layer not set')
            return
        scene_name = sceneName()
        def_scene_name = '_'.join([(sceneName().basename() or 'untitled'), 'afrender', layer.name(), id])+'.ma'
        newName = os.path.join(folder,def_scene_name).replace('\\','/')
        renameFile(newName)
        saveFile()
        renameFile(scene_name)
        return newName

    def result_output_folder(self):
        if shutgun_submit.is_valid:
            name = 'review_%s' % datetime.datetime.now().date().strftime("%Y_%m_%d")
            dir = self.output_path_le.text()
            if not dir:
                return False
            if not os.path.exists(dir):
                try:
                    os.makedirs(dir)
                except:
                    return

            exists = [x for x in os.listdir(dir) if x.startswith(name)]
            d = 1
            if exists:
                for e in exists:
                    m = re.findall(r"%s_(\d+)$" % name, e)
                    if m:
                        d = max(d, int(m[0]))
            name = name + '_%s' % str(d).zfill(3)
            f = os.path.join(dir, name ).replace('\\','/')
            while os.path.exists(f):
                f = incrementSaveName(f)
            return f
        else:
            return self.output_path_le.text()

    def default_job_name(self):
        return  'Preview Render %s' % self.session_id

    def send_to_afanasy(self, datafiles, outdir):
        import af
        pyth = os.path.join(os.getenv('CGRU_LOCATION'),'python', 'python.exe').replace('/','\\')
        jobid = self.session_id
        job = af.Job(self.af_job_name_le.text() or self.default_job_name())

        job_host_mask = self.af_host_mask_le.text()
        if job_host_mask:
            job.setHostsMask(job_host_mask)

        job_depend = self.af_job_depend_mask_le.text()
        if job_depend:
            job.setDependMask(job_depend)

        for data in datafiles:
            # bloks = []
            if data['data']['engine'] == 'ai':
                renderer = os.path.join(os.path.dirname(__file__), 'renderer', 'renderer_ai.py').replace('\\','/')
                cmd = ' '.join([pyth, renderer, ' ']).replace('/','\\')
                for i, range in enumerate(data['data']['ranges']):
                    block_render = af.Block('%s_Render_AI' % data['data']['id'], 'amg')
                    block_render.setWorkingDirectory(data['data']['tmpdir'])
                    rcmd = cmd + '%s %s @#@ @#@ ' % (data['path'], i)
                    block_render.setCommand(rcmd)
                    block_render.setNumeric(range['start'], range['end'], 1)
                    job.blocks.append(block_render)
            elif data['data']['engine'] in ['blast', 'hw']:
                # block render ogl
                renderer = os.path.join(os.path.dirname(__file__), 'renderer', 'renderer_ogl.py').replace('\\','/')
                cmd = ' '.join([pyth, renderer, ' ']).replace('/','\\')
                block_render = af.Block('%s_Render_OGL' % data['data']['id'], 'amg')
                block_render.setWorkingDirectory(data['data']['tmpdir'])
                for i, range in enumerate(data['data']['ranges']):
                    task = af.Task('Render (%s - %s)' % (range['start'], range['end']))
                    rcmd = cmd + '%s %s' % (data['path'], i)
                    task.setCommand(rcmd)
                    block_render.tasks.append(task)
                job.blocks.append(block_render)
                # todo: add HOST depend for OGL render
            else:
                PopupError('Engine not support :%s' % data['data']['engine'] )
                return
            # stamping
            if data['data']['stamp']:
                renderer = os.path.join(os.path.dirname(__file__), 'renderer', 'render_stamp.py').replace('\\','/')
                cmd = ' '.join([pyth, renderer, data['path']])
                block_stamp = af.Block('%s_Stamping' % data['data']['id'], 'amg')
                block_stamp.setDependMask('%s_Render_.*' % data['data']['id'])
                block_stamp.setCapacity(200)
                block_stamp.setWorkingDirectory(data['data']['tmpdir'])
                task = af.Task('Stamping')
                task.setCommand(cmd)
                block_stamp.tasks.append(task)
                job.blocks.append(block_stamp)
            # movie
            if data['data']['ismove']:
                # block ffmpeg
                renderer = os.path.join(os.path.dirname(__file__), 'renderer', 'renderer_mp4.py').replace('\\','/')
                cmd = ' '.join([pyth, renderer, data['path']])
                block_ffmpeg = af.Block('%s_Images_to_movie'  % data['data']['id'], 'amg')
                block_ffmpeg.setWorkingDirectory(data['data']['tmpdir'])
                block_ffmpeg.setCapacity(200)
                task = af.Task('Images to MP4')
                task.setCommand(cmd)
                block_ffmpeg.tasks.append(task)
                block_ffmpeg.setDependMask('%s_Stamping' % data['data']['id'])
                job.blocks.append(block_ffmpeg)


        postscript = os.path.join(os.path.dirname(__file__), 'post_command.py').replace('\\','/')
        tmp = self.global_output_folder()
        datafile = os.path.join(tmp, 'submit_data_%s' % jobid + '.json')
        datafile_content = json.load(open(os.path.join(os.path.dirname(__file__), 'tools', 'submit_datafile_example.json')))
        datafile_content['datafiles'] = [x['path'] for x in datafiles]
        datafile_content['context_path'] = sceneName().dirname()
        datafile_content['review_path'] = outdir
        datafile_content['id'] = jobid
        # datafile_content['comment'] = self.comment_le.toPlainText()
        datafile_content['context'] = self.ctx
        json.dump(datafile_content, open(datafile, 'w'), indent=2)

        block_post = af.Block('Post Command')
        block_post.setWorkingDirectory(tmp)
        block_post.setDependMask('.*')

        cmd = ' '.join([pyth, postscript, datafile])
        task1 = af.Task('Post Process')
        task1.setCommand(cmd)
        block_post.tasks.append(task1)

        # publichscript = os.path.join(os.path.dirname(__file__), 'renderer', 'sg_publish.py').replace('\\','/')
        # cmd = ' '.join([pyth, publichscript, datafile])
        # task2 = af.Task('Shotgun Submit')
        # task2.setCommand(cmd)
        # block_post.tasks.append(task2)

        cleanscript = os.path.join(os.path.dirname(__file__), 'renderer', 'clean.py').replace('\\','/')
        postcmd = ' '.join([pyth, cleanscript, datafile]).replace('\\','/')
        # print postcmd
        # job.setCmdPost(postcmd)
        job.blocks.append(block_post)
        if self.af_paused_cbx.isChecked():
            job.pause()
        job.send()
        self.clear_session_id()
        if amg_sender:
            amg_sender.AMGSender.send(datafile_content['review_path'], amg_sender.CMD.WATCH_RENDER_RESULT )

    def submit_local(self, datafiles, outdir):
        datafile_content = json.load(open(os.path.join(os.path.dirname(__file__), 'tools', 'submit_datafile_example.json')))
        datafile_content['datafiles'] = [x['path'] for x in datafiles]
        datafile_content['context_path'] = sceneName().dirname()
        datafile_content['review_path'] = outdir
        datafile_content['id'] = self.session_id
        datafile_content['context'] = self.ctx
        if self.post_cmd_cbb.currentIndex() == 1:
            datafile_content['postcmd'] = 'explorer ' + outdir.replace('/','\\')
        datafile = os.path.join(self.global_output_folder(), 'submit_data_%s' % self.session_id + '.json').replace('/','\\')
        json.dump(datafile_content, open(datafile, 'w'), indent=2)
        renderer = os.path.join(os.path.dirname(__file__), 'renderer', 'local_renderer.py').replace('/','\\')
        cmd = self.get_maya_locaion().replace('/','\\') + r'\bin\mayapy'
        cmd = '"%s"' % cmd
        cmd += ' %s -d %s' % (renderer, datafile)
        if self.local_paused_cbx.isChecked():
            cmd += ' -p 1'
        if QApplication.keyboardModifiers() == Qt.ShiftModifier:
            cmd += ' -c 1'
        QProcess.startDetached(cmd)
        print cmd
        # informBox('AMG Asset Submitter', 'Job is submitter to localhost', 'OK')
        self.clear_session_id()
        if amg_sender:
            r = amg_sender.AMGSender.send(outdir, amg_sender.CMD.WATCH_RENDER_RESULT)

    ############################################################### PREVIEW

    def render_current_frame_ogl(self):
        cam = self.render_camera_cbb.currentText()
        if not objExists(cam):
            warning('Camera not found')
            return
        cam = PyNode(cam)
        d = tempfile.gettempdir()
        outfile = join(d,'preview_image_%s' % random.randrange(10000, 99999)) + '.jpg'
        layer = nt.RenderLayer.currentLayer()
        engine = 'blast'
        if layer.hasAttr(shaders.oglEngineAttrName):
            engine = layer.attr(shaders.oglEngineAttrName).get()
        resolution = self.get_resolution()
        result =  render_ogl.render_current_frame_ogl(resolution, outfile.replace('/','\\'), engine, cam)
        return result

    def render_current_frame_ai(self):
        cam = PyNode(self.render_camera_cbb.currentText())
        if not objExists(cam):
            warning('Camera %s not found!' % self.render_camera_cbb.currentText())
            return
        ass = render_ai.export_temp_frame(self.get_resolution(), cam)
        # render jpg
        image = render_ai.render_ass(ass, remove_ass=True)
        return image

    def open_preview(self):
        if self.renderer_tab_tbw.currentIndex() == TAB_AI:
            frame = self.render_current_frame_ai()
        elif self.renderer_tab_tbw.currentIndex() == TAB_OGL:
            frame = self.render_current_frame_ogl()
        if self.previewWidget:
            self.previewWidget.close()
            # return
        data = self.get_stamp_data()

        self.previewWidget = preview_widget.PreviewWidget(frame, True, data=data, add_stamp=self.add_frame_stamp_cbx.isChecked(), parent=self)
        def resetPreview(pos):
            self.previewGeo = pos
            self.previewWidget = None
        self.previewWidget.closeSignal.connect(resetPreview)
        if self.previewGeo:
            self.previewWidget.setGeometry(self.previewGeo)
        self.previewWidget.show()

    # tests
    def __open_render_view(self):
        editor = cmds.renderWindowEditor(q=True, editorName=True )
        if( len(editor) == 0  ):
            editor = cmds.renderWindowEditor( "renderView" )
        runtime.RenderViewWindow()
        e = ui.RenderWindowEditor(editor)
        return e

    def __show_preview_OLD(self):
        self.editor = self.__open_render_view()
        # load images
        self.editor.loadImage('G:/english.jpg')
        QTimer.singleShot(150, self.editor.setFrameImage )

############################################################### STAMP

    def open_stamp_options(self):
        # data = self.get_stamp_data()
        if self.stamp_opt_window.isVisible():
            self.stamp_opt_window.activateWindow()
        self.stamp_opt_window.show()

    def get_stamp_data(self):

        # if self.stamp_data_tw.currentIndex() == 0:
        if self.stamp_mode_asset_rb.isChecked():
            # asset
            stampdata = dict(
            tl=[ # top left
                ['Project',   self.stamp_asset_project_le.text()],
                ['Artist',    self.stamp_asset_user_le.text()   ],
                ['Date',      self.stamp_asset_date_le.text()   ]
            ],
            tm=[ # top middle
            ],
            tr=[ # top right (logo)
            ],
            bl=[ # bottom left
                ['Asset',       self.stamp_asset_name_le.text() ],
                ['Version',     self.stamp_asset_version_le.text(),],
                ['Step',      self.stamp_asset_step_le.text(),     ],
                ['Task',      self.stamp_asset_task_le.text(),     ],
            ],
            bm=[ # bottom middle
                # ['',          'EP029sh-0030', ],
                # ['',          'v005'          ],
            ],
            br=[ # bottom right

            ]
            )
            if self.stamp_asset_frame_cbx.isChecked():
                stampdata['br'].append(['Frame', '{frame:%s}' % len(str(int(env.getAnimEndTime())))          ])
        else:
            # sequence
            stampdata = dict(
            tl=[ # top left
                ['Project',   self.stamp_squens_project_le.text()      ],
                ['Artist',    self.stamp_squens_user_le.text()      ],
                ['Date',      self.stamp_squens_date_le.text()    ]
            ],
            tm=[ # top middle
            ],
            tr=[ # top right (logo)
            ],
            bl=[ # bottom left
                ['Sequence',  self.stamp_squens_name_le.text()        ],
                ['Shot',      self.stamp_squens_shot_le.text(),       ],
                ['Step',      self.stamp_squens_step_le.text(),       ],
                ['Task',      self.stamp_squens_task_le.text(),       ],
            ],
            bm=[ # bottom middle
                ['',          self.stamp_squens_name_le.text()+self.stamp_squens_shot_le.text(), ],
                ['',          self.stamp_squens_version_le.text()     ],
            ],
            br=[ # bottom right
                ['Frame',     '{frame:%s}' % len(str(int(env.getAnimEndTime())))           ]
            ]
        )


        data = self.stamp_opt_window.get_data()
        data.update(dict(stamp=stampdata))
        return data

    def update_previewer_stamp_data(self):
        if self.previewWidget:
            data = self.get_stamp_data()
            self.previewWidget.update_stamp(data, self.add_frame_stamp_cbx.isChecked())
    pass

################################################################ OTHER

    def update_info(self):
        pass
        # print 'INFO'


def find_file(node):
    for f in node.inputs():
        if f.type() == 'file':
            return f
        return find_file(f)

def incrementSaveName(path, padding=3):
    bname = os.path.basename(path)
    dname = os.path.dirname(path)
    name, ext = os.path.splitext(bname)
    r = re.match(r"(.*?)(\d+)$", name)
    if r:
        n, d = r.groups()
        name = n + str(int(d)+1).zfill(len(d))
        result = os.path.join(dname, name+ext).replace('\\','/')
    else:
        result = os.path.join(dname, name+ '_%s' % str(1).zfill(padding)+ext).replace('\\','/')
    return result

def generate_id():
    return str(random.randrange(100000,999999))