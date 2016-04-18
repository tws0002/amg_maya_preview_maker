from pymel.core import *
from .. import submitter_variables as v
reload(v)



def get_set(create=True):
    if objExists(v.object_set_name):
        return PyNode(v.object_set_name)
    else:
        if create:
            s = createNode('objectSet', name=v.object_set_name)
            return s

def content():
    s = get_set(False)
    if s:
        objs = s.elements()
        r = v.root_group()
        return [x for x in objs if not x.root() == r]
    else:
        return []


def add_to_set(objects):
    s = get_set()
    if isinstance(objects, list):
        s.addMembers(objects)
    else:
        s.addMembers([objects,])

def remove_from_set(objects):
    s = get_set()
    to_remove = [x for x in objects if x in s.elements()]
    if to_remove:
        s.removeMembers(to_remove)

