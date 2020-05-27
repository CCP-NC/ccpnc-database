import re
import json
from datetime import datetime
from collections import namedtuple
from gridfs import GridFS, NoFile
from bson.objectid import ObjectId
from bson.errors import InvalidId
from pymongo import ReturnDocument

from ccpncdb.utils import (read_magres_file, extract_formula,
                           extract_stochiometry, extract_molecules,
                           extract_nmrdata)
from ccpncdb.schemas import (magresVersionSchema,
                             magresRecordSchema,
                             validate_with)
from ccpncdb.archive import MagresArchive
from ccpncdb.search import build_search

MagresDBAddResult = namedtuple('MagresDBAddResult',
                               ['successful', 'id', 'mdbref'])


class MagresDBError(Exception):
    pass


class MagresDB(object):

    def __init__(self, client, dbname='ccpnc'):

        self.client = client
        ccpnc = self.client[dbname]

        # Grab the collections
        #
        # 1. GridFS collection for magres files
        self.magresFilesFS = GridFS(ccpnc, 'magresFilesFS')
        # 2. Searchable data, including multiple versions (and references to
        # files)
        self.magresIndex = ccpnc.magresIndex
        # 3. Unique ID counter
        self.magresIDcount = ccpnc.magresIDcount

    def _auto_recdata(self, matoms):
        # Compute a dictionary of all data that needs to be extracted
        # automatically from a magres Atoms object
        formula = extract_formula(matoms)
        mols = extract_molecules(matoms)

        autodata = {
            'formula': formula,
            'stochiometry': extract_stochiometry(formula),
            'molecules': mols,
            'Z': len(mols),
            'nmrdata': extract_nmrdata(matoms)
        }

        return autodata

    def add_record(self, mfile, record_data, version_data):

        # Read in magres file
        magres = read_magres_file(mfile)
        mstr = magres['string']
        matoms = magres['Atoms']

        # Generate automated data
        record_autodata = {
            'visible': True,
            'mdbref': '0000000',            # Placeholder
            'version_count': 0,
            'version_history': []          # Empty for now
        }

        record_autodata.update(self._auto_recdata(matoms))

        record_data = dict(record_data)
        record_data.update(record_autodata)
        valres = validate_with(record_data, magresRecordSchema)
        if not valres.result:
            if valres.invalid is None:
                # Missing keys
                raise MagresDBError('Missing keys: ' +
                                    ', '.join(valres.missing))
            else:
                # Invalid key
                raise MagresDBError('Invalid key: ' + valres.invalid)

        # Add the record to the database
        res = self.magresIndex.insert_one(record_data)
        if not res.acknowledged:
            raise MagresDBError('Unknown error while uploading record')
        record_id = res.inserted_id
        # Finally, the version data
        self.add_version(record_id, mstr, version_data, False)
        # Now that it's all done, assign a unique identifier
        mdbref = self.generate_id()
        # Update the record
        res = self.magresIndex.update_one({'_id': ObjectId(record_id)},
                                          {'$set': {'mdbref': mdbref}})

        return MagresDBAddResult(res.acknowledged, str(record_id), mdbref)

    def add_version(self, record_id,
                    mfile=None, version_data={}, update_record=True):

        # Read in magres file
        if mfile is None:
            # Just get the contents from the record
            rec = self.get_record(record_id)
            if rec['version_count'] == 0:
                raise MagresDBError('A magres file must be passed for the '
                                    'first version of a record')
            mfile_id = rec['last_version']['magresFilesID']
            calc_block = rec['last_version']['magres_calc']
        else:
            magres = read_magres_file(mfile)
            mstr = magres['string']
            matoms = magres['Atoms']

            mfile_id = self.magresFilesFS.put(mstr,
                                              filename=record_id,
                                              encoding='UTF-8')
            calc_block = json.dumps(matoms.info.get(
                'magresblock_calculation',
                {}))

        version_autodata = {
            'magresFilesID': str(mfile_id),
            'date': datetime.utcnow(),
            'magres_calc': calc_block
        }

        version_data = dict(version_data)
        version_data.update(version_autodata)
        valres = validate_with(version_data, magresVersionSchema)
        if not valres.result:
            if valres.invalid is None:
                # Missing keys
                raise MagresDBError('Missing keys: ' +
                                    ', '.join(valres.missing))
            else:
                # Invalid key
                raise MagresDBError('Invalid key: ' + valres.invalid)

        to_set = {'last_version': version_data}

        if update_record and mfile is not None:
            # Update the automatically generated elements in the record
            to_set.update(self._auto_recdata(matoms))

        res = self.magresIndex.update_one({'_id': ObjectId(record_id)},
                                          {'$push': {
                                              'version_history':
                                              version_data
                                          },
            '$inc': {'version_count': 1},
            '$set': to_set
        })

        if not res.acknowledged:
            raise MagresDBError('Could not push new version for record ' +
                                str(record_id))

    def add_archive(self, archive, record_data, version_data):

        # Create an archive object
        ma = MagresArchive(archive, record_data, version_data)
        results = {}

        # Iterate over files
        for f in ma.files():
            results[f.name] = self.add_record(f.contents,
                                              f.record_data,
                                              f.version_data)

        return results

    def edit_record(self, record_id, update):

        res = self.magresIndex.update_one({'_id': ObjectId(record_id)},
                                          update=update)

        return res.acknowledged

    def get_record(self, record_id):

        try:
            mrec = self.magresIndex.find_one({'_id': ObjectId(record_id)})
        except InvalidId:
            raise MagresDBError('Invalid ID requested')

        if mrec is None:
            raise MagresDBError('Record not found')

        return mrec

    def get_magres_file(self, fs_id, decode=False):

        try:
            mfile_ref = self.magresFilesFS.get(ObjectId(fs_id))
        except NoFile:
            raise MagresDBError('File not found')

        if decode:
            return mfile_ref.read().decode('utf-8')
        else:
            return mfile_ref.read()

    def search_record(self, query):
        query = build_search(query)

        results = self.magresIndex.find(query)

        return results

    def generate_id(self):
        # Generate a new unique ID
        res = self.magresIDcount.find_one_and_update(
            filter={},
            return_document=ReturnDocument.AFTER,
            update={'$inc': {'count': 1}},
            upsert=True)
        mdbid = res['count']
        # Format as string
        mdbid = '{0:07d}'.format(mdbid)

        return mdbid
