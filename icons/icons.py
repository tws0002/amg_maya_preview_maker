import os
from ..preferences import join

root = os.path.dirname(__file__)

icons = dict(
    checked=join(root, 'checked.png'),
    unchecked=join(root, 'unchecked.png')
)