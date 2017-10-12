import tempfile
import numpy as np
from ase import io
from soprano.properties.nmr import MSIsotropy
from pymongo import MongoClient


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


def searchByMS(sp, minms, maxms):

    client = MongoClient(host='wigner.esc.rl.ac.uk')
    ccpnc = client.ccpnc

    ff = ccpnc.magresData.find({"$and": [
        {"values": {"$elemMatch": {"species": sp}}},
        {"values": {"$elemMatch":
                    {"$nor": [{"iso": {"$lt": minms}},
                              {"iso": {"$gt": maxms}}]}
                    }
         }
    ]})

    # Return the data

    fileIDs = [{'chemname': f.get('chemname', 'N/A'),
                'orcid': f.get('orcid', 'N/A')}
               for f in ff]

    return json.dumps(fileIDs)


def addMagresFile(magresStr, metadata={}):
    client = MongoClient(host='wigner.esc.rl.ac.uk')
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

    import sys

    addMagresFile(open(sys.argv[1]).read(), {'dummy': 0})
