import json
import inspect
import tempfile
import numpy as np
from ase import io
from soprano.properties.nmr import MSIsotropy
from pymongo import MongoClient
from schema import SchemaError
from gridfs import GridFS
from db_schema import (magresDataSchema,
                       magresVersionSchema,
                       magresMetadataSchema)

_db_url = 'wigner.esc.rl.ac.uk'
#_db_url = 'localhost:9000'

### METHODS FOR COMPILATION OF METADATA ###


def getMSMetadata(magres):

    msdata = {}

    # Chemical species
    symbols = np.array(magres.get_chemical_symbols())
    sp = {s: np.where(symbols == s) for s in set(symbols)}
    isos = MSIsotropy.get(magres)

    msdata['values'] = [{'species': s,
                         'iso': list(isos[inds])}
                        for s, inds in sp.iteritems()]

    return msdata

### UPLOADING ###


def addMagresFile(magresStr, chemname, orcid, data={}):
    client = MongoClient(host=_db_url)
    ccpnc = client.ccpnc

    # Three collections:
    # 1. GridFS collection for magres files
    magresFilesFS = GridFS(ccpnc, 'magresFilesFS')
    # 2. Metadata collection (one element per database entry,
    # including history)
    magresMetadata = ccpnc.magresMetadata
    # 3. Searchable data, updated when the other two change, to the latest
    # version
    magresIndex = ccpnc.magresIndex

    with tempfile.NamedTemporaryFile(suffix='.magres') as f:
        f.write(magresStr)
        f.flush()
        # WARNING: this will only work on a UNIX system! Apparently does not
        # work on Windows NT and above. More details at
        # https://docs.python.org/2/library/tempfile.html#tempfile.NamedTemporaryFile
        magres = io.read(f.name)

    #d = data
    #d.update(getMSMetadata(magres))

    # Validate metadata
    metadata = {
        'chemname': chemname,
        'orcid': orcid,
        'version_history': []
    }
    metadata = magresMetadataSchema.validate(metadata)

    # Create first version (with dummy ID) and validate
    version = {
        'magresFilesID': 'dummy'
    }
    version.update(data)
    version = magresVersionSchema.validate(version)

    # Now on to the data posting. We start with the metadata
    magresMetadataInsertion = magresMetadata.insert_one(metadata)
    magresMetadataID = magresMetadataInsertion.inserted_id
    # Then we move on to the GridFS storage of the file itself
    magresFilesID = magresFilesFS.put(magresStr, filename=magresMetadataID)
    # And cross-reference
    version['magresFilesID'] = magresFilesID
    magresMetadataUpdate = magresMetadata.update_one({'_id':
                                                      magresMetadataID},
                                                     {'$push': {
                                                         'version_history':
                                                         version
                                                     }})
    # Now create the searchable dictionary
    

    # Return True only if all went well
    return (magresMetadataInsertion.acknowledged and
            (magresFilesID is not None) and
            magresMetadataUpdate.modified_count)

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
        'doi': searchByDOI,
        'orcid': searchByOrcid,
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
            args = {a: src['args'][a] for a in args}
        except KeyError:
            raise ValueError('400 Bad Request - Invalid search spec')

        search_dict['$and'] += search_func(**args)

    # Carry out the actual search
    results = ccpnc.magresData.find(search_dict)

    return json.dumps([makeEntry(f)
                       for f in results])

# Specific search functions


def searchByMS(sp, minms, maxms):

    return [
        {'values': {'$elemMatch': {'species': sp}}},
        {'values': {'$elemMatch':
                    {'$nor': [{'iso': {'$lt': float(minms)}},
                              {'iso': {'$gt': float(maxms)}}]}
                    }
         }
    ]


def searchByDOI(doi):

    return [
        {'doi': doi}
    ]


def searchByOrcid(orcid):

    return [
        {'orcid.path': orcid}
    ]
