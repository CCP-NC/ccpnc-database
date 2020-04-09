from io import StringIO
from ase.io.magres import read_magres


def readMagres(mfile):
    # Read a magres file/string unifying the output into an ASE Atoms object
    if hasattr(mfile, 'read'):
        mstr = mfile.read()
    else:
        mstr = mfile
    # Safety required for Python 3
    if (hasattr(mstr, 'decode')):
        mstr = mstr.decode()
    magres = read_magres(StringIO(str(mstr)))

    return magres
