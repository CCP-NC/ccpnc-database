import os
import sys

path = os.path.split(__file__)[0]

sys.path.append(os.path.join(path, '..'))


_fake_orcid = {
    'path': '0000-0000-0000-0000',
    'host': 'none',
    'uri': '0000-0000-0000-0000'
}

with open(sys.argv[1]) as f:

    from db_interface import addMagresFile

    chemname = os.path.splitext(os.path.basename(sys.argv[1]))[0]

    addMagresFile(f, chemname, '', 'pddl', _fake_orcid)
