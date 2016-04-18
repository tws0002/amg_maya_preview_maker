import os, json

def presets_folder():
    return os.path.join(os.path.dirname(__file__), 'shaders').replace('\\','/')


def get_presets():
    shaders = []
    root = presets_folder()
    for s in root:
        if os.path.splitext(s)[-1] == '.json':
            data = json.load(open(os.path.join(root, s)))
            shaders.append(data)
    return shaders
