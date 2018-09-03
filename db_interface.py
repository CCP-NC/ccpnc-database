import os
import re
import csv
import json
import inspect
import tempfile
import numpy as np
import zipfile
import tarfile
import StringIO
from copy import deepcopy

from ase import io
from datetime import datetime
from ase.io.magres import read_magres
from soprano.properties.nmr import MSIsotropy

from pymongo import MongoClient
from schema import SchemaError
from gridfs import GridFS, NoFile
from bson.objectid import ObjectId
from db_schema import (magresVersionSchema,
                       magresMetadataSchema,
                       magresIndexSchema)

try:
    config = json.load(open(os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "config", "config.json"),
        "r"))
except IOError:
    config = {}

_db_url = config.get("db_url", "localhost")
_db_port = config.get("db_port", 27017)

# Convenient tool to turn a magres string into an ase.Atoms object


class MagresStrCast(object):

    def __init__(self, mstr):
        self._mstr = mstr

    def read(self):
        return self._mstr

    def atoms(self):
        return read_magres(self)

### METHODS FOR COMPILATION OF METADATA ###


def getFormula(magres):

    symbols = magres.get_chemical_symbols()
    formula = [{'species': s, 'n': symbols.count(s)} for s in set(symbols)]
    formula = sorted(formula, key=lambda x: x['species'])

    return formula


def getMSMetadata(magres):

    # Chemical species
    symbols = np.array(magres.get_chemical_symbols())
    sp = {s: np.where(symbols == s) for s in set(symbols)}
    isos = MSIsotropy.get(magres)

    msdata = [{'species': s,
               'iso': list(isos[inds])}
              for s, inds in sp.iteritems()]

    return msdata


def getDBCollections():
    # Return the database's collections after establishing a connection
    client = MongoClient(host=_db_url, port=_db_port)
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

    return magresFilesFS, magresMetadata, magresIndex


### UPLOADING ###


def addMagresFile(magresFd, chemname, orcid, data={}):

    # Inserts a file, returns index id if successful, otherwise False

    magresFilesFS, magresMetadata, magresIndex = getDBCollections()

    magres = read_magres(magresFd)
    magresFd.seek(0)
    magresStr = magresFd.read()

    # Validate metadata
    metadata = {
        'chemname': chemname,
        'orcid': orcid,
        'version_history': []
    }
    metadata = magresMetadataSchema.validate(metadata)

    # Create first version (with dummy ID) and validate
    version = {
        'magresFilesID': 'dummy',
        'date': datetime.utcnow()
    }
    version.update(data)
    version = magresVersionSchema.validate(version)

    # Now on to the data posting. We start with the metadata
    magresMetadataInsertion = magresMetadata.insert_one(metadata)
    magresMetadataID = magresMetadataInsertion.inserted_id
    # Then we move on to the GridFS storage of the file itself
    magresFilesID = magresFilesFS.put(magresStr, filename=magresMetadataID,
                                      encoding='UTF-8')
    # And cross-reference
    version['magresFilesID'] = str(magresFilesID)
    magresMetadataUpdate = magresMetadata.update_one({'_id':
                                                      magresMetadataID},
                                                     {'$push': {
                                                         'version_history':
                                                         version
                                                     }})
    # Now create the searchable dictionary
    index = {
        'chemname': metadata['chemname'],
        'orcid': metadata['orcid'],
        'metadataID': str(magresMetadataID),
    }
    index['formula'] = getFormula(magres)
    index['values'] = getMSMetadata(magres)
    index['latest_version'] = version
    index = magresIndexSchema.validate(index)

    magresIndexInsertion = magresIndex.insert_one(index)

    # Return ID only if all went well
    if ((magresMetadataInsertion.acknowledged and
         magresIndexInsertion.acknowledged and
         (magresFilesID is not None) and
         magresMetadataUpdate.modified_count)):
        return magresIndexInsertion.inserted_id
    else:
        return False


def addMagresArchive(archive, chemname, orcid, data={}):
    """
    Uploads a full archive containing magres files.
    Returns 0 for full success, 1 for some errors, 2 for total failure;
    then returns a dict of all ids for successfully added files
    (False for failed ones)
    """

    fileList = {}

    try:
        with zipfile.ZipFile(archive) as z:
            for n in z.namelist():
                name = os.path.basename(n)
                if len(name) > 0:
                    with z.open(n) as f:
                        fileList.update({name: f.read()})
    except zipfile.BadZipfile:
        archive.seek(0) # Clear
        try:
            with tarfile.open(fileobj=archive) as z:
                for ti in z.getmembers():
                    if ti.isfile():
                        f = z.extractfile(ti)
                        fileList.update({os.path.basename(ti.name): f.read()})
                        f.close()
        except tarfile.ReadError:
            raise RuntimeError(
                'Uploaded archive file is not a valid zip or tar file.')

    # The passed data is used as a default
    # Anything else we get from the .csv

    info = [f for name, f in fileList.items()
            if os.path.splitext(name.lower())[1] == '.csv']
    magresList = {name: f for name, f in fileList.items()
                  if os.path.splitext(name.lower())[1] == '.magres'}

    if len(info) > 1:
        raise RuntimeError(
            'Uploaded archive file must contain at most a single .csv file')
    elif len(info) == 0:
        csvReader = []  # Dummy
    else:
        csvReader = csv.DictReader(info[0].splitlines())

    default_args = {'orcid': orcid,
                    'chemname': chemname,
                    'data': data.copy()}
    argdict = {}

    for entry in csvReader:
        # File column is obligatory
        try:
            fname = entry.pop('filename')
        except KeyError:
            raise RuntimeError('Invalid CSV file used in archive')

        # Is the file valid?
        if os.path.splitext(fname)[1] != '.magres':
            raise RuntimeError('File referenced in .csv is not a .magres file')
        if fname not in magresList:
            raise RuntimeError(
                'Could not find {0} in the archive'.format(fname))

        # Ok, we're ready to go
        argdict[fname] = deepcopy(default_args)
        argdict[fname]['chemname'] = entry.pop('chemname', chemname)
        argdict[fname]['data'].update(entry)

    added_ids = {}
    success_code = 0
    for f, magresStr in magresList.items():
        args = argdict.get(f, default_args)
        ind_id = addMagresFile(magresStr, **args)
        if not ind_id:
            success_code = 1
        added_ids[f] = ind_id

    success_code += (len(added_ids) == 0)

    return success_code, added_ids


def editMagresFile(index_id, orcid, data={}, magresStr=None):

    magresFilesFS, magresMetadata, magresIndex = getDBCollections()

    # Retrieve the entry from the index
    magresIndexID = ObjectId(index_id)
    index_entry = magresIndex.find_one({'_id': magresIndexID})

    if orcid != index_entry['orcid']:
        raise RuntimeError('Entry is not owned by user')

    if index_entry is None:
        raise RuntimeError('No entry to edit found')

    # Now the metadata
    magresMetadataID = ObjectId(index_entry['metadataID'])
    mdata_entry = magresMetadata.find_one({'_id': magresMetadataID})

    if mdata_entry is None:
        raise RuntimeError('Metadata missing for requested entry')

    # Now, if there's a new file, upload it, otherwise use the last one
    if magresStr is not None:
        # Check that the formula is right

        magres = MagresStrCast(magresStr).atoms()

        formula = getFormula(magres)
        if index_entry['formula'] != formula:
            raise RuntimeError('Invalid Magres File for editing '
                               '(different compound)')

        magresFilesID = magresFilesFS.put(magresStr,
                                          filename=index_entry['metadataID'],
                                          encoding='UTF-8')
    else:
        magresFilesID = index_entry['latest_version']['magresFilesID']

    # Create the new version
    version = {
        'magresFilesID': str(magresFilesID),
        'date': datetime.utcnow()
    }
    version.update(data)
    version = magresVersionSchema.validate(version)

    # Then update the metadata
    magresMetadataUpdate = magresMetadata.update_one({'_id':
                                                      magresMetadataID},
                                                     {'$push': {
                                                         'version_history':
                                                         version
                                                     }})
    # And update the index
    magresIndexUpdate = magresIndex.update_one({'_id': magresIndexID},
                                               {'$set': {
                                                   'latest_version': version
                                               }})

    # Return True only if all went well
    return (magresMetadataUpdate.modified_count and
            magresIndexUpdate.modified_count)


def getMagresFile(file_id):

    magresFilesFS, magresMetadata, magresIndex = getDBCollections()

    try:
        mfile_ref = magresFilesFS.get(ObjectId(file_id))
    except NoFile:
        return None

    return mfile_ref.read()


def removeMagresFiles(index_id):
    # Only used for debug, should not be exposed to users

    magresFilesFS, magresMetadata, magresIndex = getDBCollections()

    try:
        index_entry = magresIndex.find({'_id': ObjectId(index_id)}).next()
    except StopIteration:
        raise RuntimeError('No entry with that id found')
    # Find metadata
    mdata_entry = magresMetadata.find({'_id':
                                       ObjectId(index_entry[
                                           'metadataID'])}).next()
    # Find and remove magres files
    for v in mdata_entry['version_history']:
        magresFilesFS.delete(v['magresFilesID'])
    magresMetadata.delete_one({'_id': ObjectId(index_entry['metadataID'])})
    magresIndex.delete_one({'_id': ObjectId(index_id)})


if __name__ == "__main__":

    # Used for testing purposes

    import sys

    addMagresFile(open(sys.argv[1]).read(), {'dummy': 0})

### SEARCH METHODS ###


def makeEntry(ind, meta):
    # From database record to parsable entry
    try:
        entry = {
            'chemname': ind['chemname'],
            'orcid': ind['orcid']['path'],
            'formula': ''.join(map(lambda x: x['species'] + str(x['n']),
                                   ind['formula'])),
            'orcid_uri': ind['orcid']['uri'],
            'version_history': meta['version_history'],
            'index_id': ind['_id'],
            'meta_id': meta['_id']
        }
    except KeyError:
        return None

    return entry


def databaseSearch(search_spec):

    magresFilesFS, magresMetadata, magresIndex = getDBCollections()

    # List search functions
    search_types = {
        'msRange': searchByMS,
        'doi': searchByDOI,
        'orcid': searchByOrcid,
        'cname': searchByChemname
    }

    search_dict = {
        '$and': [],
    }

    # Build the string
    for src in search_spec:
        try:
            search_func = search_types[src.get('type')]
        except KeyError:
            raise ValueError('Invalid search type')

        # Find arguments
        args = inspect.getargspec(search_func).args

        # Get them as dict
        try:
            args = {a: src['args'][a] for a in args}
        except KeyError:
            raise ValueError('Invalid search arguments')

        search_dict['$and'] += search_func(**args)

    # Carry out the actual search
    resultsInd = magresIndex.find(search_dict)
    # Find the corresponding metadata
    results = []
    for rInd in resultsInd:
        oid = ObjectId(rInd['metadataID'])
        mdata = [m for m in magresMetadata.find({'_id': oid})]
        if len(mdata) != 1:
            # Wut?
            # Invalid entry; skip
            continue
        else:
            results.append((rInd, mdata[0]))

    return json.dumps([makeEntry(ind, meta)
                       for ind, meta in results], default=str)  # For dates

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
        {'latest_version.doi': doi}
    ]


def searchByOrcid(orcid):

    return [
        {'orcid.path': orcid}
    ]


def searchByChemname(pattern):

    regex = re.compile(pattern)

    return [
        {'chemname': {'$regex': regex}}
    ]
