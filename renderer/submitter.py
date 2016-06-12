from pymel.core import *


def send_to_afanasy():
    from amg.af import af_util
    if not af_util.server_is_started():
        PopupError('Afanasy server not started')
        return

def local_render():
    pass