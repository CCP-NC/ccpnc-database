from datetime import datetime
from collections import namedtuple
from gridfs import GridFS, NoFile
from pymongo import MongoClient, ReturnDocument

from ccpncdb.config import Config
from ccpncdb.utils import (read_magres_file, extract_formula,
                           extract_stochiometry, extract_molecules,
                           extract_nmrdata)
from ccpncdb.schemas import (magresIndexSchema,
                             magresMetadataSchema,
                             magresVersionSchema,
                             magresRecordSchema,
                             magresRecordSchemaUser)
from ccpncdb.archive import MagresArchive

MagresDBAddResult = namedtuple('MagresDBAddResult',
                               ['successful', 'id', 'mdbref'])


class MagresDBError(Exception):
    pass


class MagresDB(object):

    def __init__(self, dbname='ccpnc'):

        self.config = Config()
        self.client = MongoClient(host=self.config.db_url,
                                  port=self.config.db_port)
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
        # 4. Logger
        self.magresLog = ccpnc.magresLog

    def add_record(self, mfile, record_data, version_data):

        # Read in magres file
        magres = read_magres_file(mfile)
        mstr = magres['string']
        matoms = magres['Atoms']

        # Generate automated data
        formula = extract_formula(matoms)
        mols = extract_molecules(matoms)
        record_autodata = {
            'mdbref': '0000000',            # Placeholder
            'version_history': [],          # Empty for now
            'formula': formula,
            'stochiometry': extract_stochiometry(formula),
            'molecules': mols,
            'Z': len(mols),
            'nmrdata': extract_nmrdata(matoms)
        }

        record_data.update(record_autodata)
        try:
            magresRecordSchema.validate(record_data)
        except Exception as e:
            raise MagresDBError('Trying to upload invalid record: ' + str(e))

        # Add the record to the database
        res = self.magresIndex.insert_one(record_data)
        if not res.acknowledged:
            raise MagresDBError('Unknown error while uploading record')
        record_id = res.inserted_id
        # Finally, the version data
        self.add_version(mstr, record_id, version_data)
        # Now that it's all done, assign a unique identifier
        mdbref = self.generate_id()
        # Update the record
        res = self.magresIndex.update_one({'_id': record_id},
                                          {'$set': {'mdbref': mdbref}})

        return MagresDBAddResult(res.acknowledged, str(record_id), mdbref)

    def add_version(self, mstr, record_id, version_data):

        mfile_id = self.magresFilesFS.put(mstr,
                                          filename=record_id,
                                          encoding='UTF-8')

        version_autodata = {
            'magresFilesID': str(mfile_id),
            'date': datetime.utcnow()
        }
        version_data.update(version_autodata)
        try:
            magresVersionSchema.validate(version_data)
        except Exception as e:
            raise MagresDBError('Trying to upload invalid version: ' + str(e))

        res = self.magresIndex.update_one({'_id': record_id},
                                          {'$push': {
                                              'version_history': version_data
                                          }
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
