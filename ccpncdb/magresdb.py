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
                           extract_nmrdata, extract_elements,
                           extract_elements_ratios, set_null_values,
                           tokenize_name)
from ccpncdb.schemas import (magresVersionSchema,
                             magresRecordSchema,
                             validate_with)
from ccpncdb.archive import MagresArchive, MagresArchiveError
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

    def _auto_rdata(self, matoms):
        # Compute a dictionary of all data that needs to be extracted
        # automatically from a magres Atoms object
        formula = extract_formula(matoms)
        mols = extract_molecules(matoms)

        elements = extract_elements(formula)

        autodata = {
            'formula': formula,
            'stochiometry': extract_stochiometry(formula),
            'elements': elements,
            'elements_ratios': extract_elements_ratios(formula),
            'chemical_formula_descriptive': matoms.get_chemical_formula(),
            'nelements': len(elements),
            'molecules': mols,
            'Z': len(mols),
            'nmrdata': extract_nmrdata(matoms)
        }

        return autodata

    def _load_magres(self, mfile):

        # Read in magres file
        try:
            magres = read_magres_file(mfile)
        except:
            # Anything, really
            raise MagresDBError('Invalid magres file')
        return magres

    def _validate_rdata(self, magres, record_data, date=None):

        matoms = magres['Atoms']

        if date is None:
            date = datetime.utcnow()

        # Generate automated data
        record_autodata = {
            'id': 'NONE',                  # Placeholder
            'type': 'magres',
            'visible': True,
            'chemname_tokens': [''],
            'last_modified': date,
            'immutable_id': '0000000',     # Placeholder
            'version_count': 0,
            'version_history': [],          # Empty for now
            'last_version': None
        }

        record_autodata.update(self._auto_rdata(matoms))

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

        # Extract the tokens
        record_data['chemname_tokens'] = tokenize_name(record_data['chemname'])
        record_data = set_null_values(record_data, magresRecordSchema)

        return record_data

    def _push_record(self, magres, record_data, version_data):

        mstr = magres['string']
        date = record_data['last_modified']

      # Add the record to the database
        res = self.magresIndex.insert_one(record_data)
        if not res.acknowledged:
            raise MagresDBError('Unknown error while uploading record')
        record_id = res.inserted_id
        # Finally, the version data
        try:
            self.add_version(record_id, mstr, version_data, False, date)
        except MagresDBError as e:
            # Delete the record for the failed version
            self.magresIndex.delete_one({'_id': ObjectId(record_id)})
            raise e
        # Now that it's all done, assign a unique identifier
        mdbref = self.generate_id()
        # Update the record
        res = self.magresIndex.update_one({'_id': ObjectId(record_id)},
                                          {'$set': {'id': str(record_id),
                                                    'immutable_id': mdbref}})

        return MagresDBAddResult(res.acknowledged, str(record_id), mdbref)

    def _validate_vdata(self, version_data={}, date=None):

        if date is None:
            date = datetime.utcnow()

        version_autodata = {
            'magresFilesID': '000',  # Placeholder
            'date': date,
            'magres_calc': None
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

        version_data = set_null_values(version_data, magresVersionSchema)

        return version_data

    def _push_version(self, record_id, magres, version_data,
                      update_record=True):

        # Read in magres file
        if magres is None:
            # Just get the contents from the record
            rec = self.get_record(record_id)
            if rec['version_count'] == 0:
                raise MagresDBError('A magres file must be passed for the '
                                    'first version of a record')
            mfile_id = rec['last_version']['magresFilesID']
            calc_block = rec['last_version']['magres_calc']
        else:

            mstr = magres['string']
            matoms = magres['Atoms']

            mfile_id = self.magresFilesFS.put(mstr,
                                              filename=record_id,
                                              encoding='UTF-8')
            calc_block = matoms.info.get('magresblock_calculation', {})
            calc_block = (json.dumps(calc_block) if len(calc_block) > 0 else
                          None)

        date = version_data['date']

        # Set these two
        version_data['magresFilesID'] = str(mfile_id)
        version_data['magres_calc'] = calc_block

        to_set = {'last_version': version_data, 'last_modified': date}

        if update_record and magres is not None:
            # Update the automatically generated elements in the record
            to_set.update(self._auto_rdata(matoms))

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

    def add_record(self, mfile, record_data, version_data, date=None):

        # Read in magres file
        magres = self._load_magres(mfile)

        record_data = self._validate_rdata(magres, record_data, date)

        return self._push_record(magres, record_data, version_data)

    def add_version(self, record_id,
                    mfile=None, version_data={}, update_record=True,
                    date=None):

        if mfile is not None:
            magres = self._load_magres(mfile)
        else:
            magres = None

        version_data = self._validate_vdata(version_data, date)

        self._push_version(record_id, magres, version_data, update_record)

    def add_archive(self, archive, record_data, version_data):

        try:
            ma = MagresArchive(archive, record_data=record_data,
                               version_data=version_data)
        except MagresArchiveError as e:
            return ('Invalid archive: {0}'.format(e),
                    self.HTTP_400_BAD_REQUEST)

        data = {}

        results = {}

        for f in ma.files():

            magres = self._load_magres(f.contents)
            rdata = self._validate_rdata(magres, f.record_data)
            vdata = self._validate_vdata(f.version_data)
            data[f.name] = (magres, rdata, vdata)

        successful = []
        failed = []
        mdbrefs = []
        ids = []

        # If everything's gone right, we can push
        for f in ma.files():
            magres, rdata, vdata = data[f.name]
            try:
                results[f.name] = self._push_record(magres, rdata, vdata)
            except:
                results[f.name] = None

        return results

    def edit_record(self, record_id, update):

        res = self.magresIndex.update_one({'_id': ObjectId(record_id)},
                                          update=update)

        return res.acknowledged

    def set_visibility(self, record_id, visible):

        return self.edit_record(record_id, {'$set': {'visible': visible}})

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
