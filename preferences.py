import os, json

appdata = os.environ.get('APPDATA', os.path.expanduser('~')).replace('\\','/')
pref_file = 'pw_asset_submitter_prefs.json'

def join(*args):
    try:
        args = [x for x in args if isinstance(x, (str, unicode))]
    except:
        args = [x for x in args if isinstance(x, str)]
    return os.path.join(*args).replace('\\','/')

class Preferences(object):
    def __init__(self):
        super(Preferences, self).__init__()
        self.file = join(appdata, pref_file)
    def __repr__(self):
        return self.file

