'''menuData
act={name:Preview Maker,action:show()}
'''
from PySide.QtCore import QTimer
from pymel.core import pluginInfo, loadPlugin, cmds, confirmDialog, objExists, sceneName, PopupError
import submitter_variables

def load_ai():
    try:
        if not pluginInfo('mtoa.mll', q=1, l=1):
            loadPlugin('mtoa.mll')
            return True
    except:
        print 'Error load Arnold Renderer'



def show():        #check modifyed
    if not sceneName():
        PopupError('Save scene before continue')
        return
    if cmds.file(q=True, modified=True) and not objExists(submitter_variables.root_group_name):
        if confirmDialog( title='Continue ?',
                          message='Scene have unsaved changes\n\nContinue without saving?',
                          button=['Yes','No'],
                          defaultButton='Yes',
                          cancelButton='No',
                          dismissString='No' ) == 'No':
            return
    def showUI():
        from . import submitter_window
        reload(submitter_window)
        w = submitter_window.SubmitterWindowClass()
        w.show()
    load_ai()
    QTimer.singleShot(1000, showUI)
