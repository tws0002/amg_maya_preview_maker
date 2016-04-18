import json, os

def join(*args):
    try:
        args = [x for x in args if isinstance(x, (str, unicode))]
    except:
        args = [x for x in args if isinstance(x, str)]
    return os.path.join(*args).replace('\\','/')

def parentFolder(path, depth=1):
    return '/'.join(path.replace('\\','/').split('/')[:-depth])

class Config(object):
    def __init__(self):
        self.path = join(os.path.expanduser('~'),'amg_asset_previewer.json')

    def __read(self):
        if os.path.exists(self.path):
            try:
                return json.load(open(self.path))
            except:
                return {}
        else:
            return {}

    def __write(self, data):
        try:
            json.dump(data, open(self.path, 'w'), indent=2)
            return True
        except:
            return False

    def get(self):
        return self.__read()

    def set(self, key, value):
        data = self.__read()
        data[key] = value
        self.__write(data)


    def save(self, data):
        self.__write(data)
