import json
import inspect
import tempfile
import numpy as np
from ase import io
from soprano.properties.nmr import MSIsotropy
from pymongo import MongoClient

_db_url = 'wigner.esc.rl.ac.uk'

### METHODS FOR COMPILATION OF METADATA ###


def getMSMetadata(magres):

    msdata = {}

    # Chemical species
    symbols = np.array(magres.get_chemical_symbols())
    sp = {s: np.where(symbols == s) for s in set(symbols)}
    isos = MSIsotropy.get(magres)

    msdata["values"] = [{'species': s,
                         'iso': list(isos[inds])}
                        for s, inds in sp.iteritems()]

    return msdata

### UPLOADING ###


def addMagresFile(magresStr, metadata={}):
    client = MongoClient(host=_db_url)
    ccpnc = client.ccpnc

    # get the magresFiles collection from the database
    magresFiles = ccpnc.magresFiles
    # get the magresData collection from the database
    magresData = ccpnc.magresData

    with tempfile.NamedTemporaryFile(suffix='.magres') as f:
        f.write(magresStr)
        f.flush()
        # WARNING: this will only work on a UNIX system! Apparently does not
        # work on Windows NT and above. More details at
        # https://docs.python.org/2/library/tempfile.html#tempfile.NamedTemporaryFile
        magres = io.read(f.name)

    d = metadata
    d.update(getMSMetadata(magres))

    # Actually post data
    magresFilesID = magresFiles.insert_one({"magres": magresStr}).inserted_id
    d["magresFilesID"] = magresFilesID
    return magresData.insert_one(d).acknowledged

if __name__ == "__main__":

    # Used for testing purposes

    import sys

    addMagresFile(open(sys.argv[1]).read(), {'dummy': 0})

### SEARCH METHODS ###

def makeEntry(f):
    # From database record to parsable entry
    try:
        entry = {
            'chemname': f['chemname'],
            'doi': f['doi']
        }
    except KeyError:
        return None

    return entry


def databaseSearch(search_spec):

    client = MongoClient(host=_db_url)
    ccpnc = client.ccpnc

    # List search functions
    search_types = {
        'msRange': searchByMS,
    }

    search_dict = {
        '$and': [],
    }

    # Build the string
    for src in search_spec:
        try:
            search_func = search_types[src.get('type')]
        except KeyError:
            raise ValueError('Invalid search spec')

        # Find arguments
        args = inspect.getargspec(search_func).args

        # Get them as dict
        try:
            args = {a: src[a] for a in args}
        except KeyError:
            raise ValueError('Invalid search spec')

        search_dict['$and'] += search_func(**args)

    # Carry out the actual search
    results = ccpnc.magresData.find(search_dict)

    return json.dumps([makeEntry(f)
                       for f in results])


def searchByMS(sp, minms, maxms):

    return [
        {'values': {'$elemMatch': {'species': sp}}},
        {'values': {'$elemMatch':
                    {'$nor': [{'iso': {'$lt': minms}},
                              {'iso': {'$gt': maxms}}]}
                    }
         }
    ]
