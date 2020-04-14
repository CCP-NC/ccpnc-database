from pymongo import MongoClient, ReturnDocument
from gridfs import GridFS, NoFile
from ccpncdb.config import Config
from ccpncdb.utils import readMagres
from ccpncdb.schemas import (magresIndexSchema,
                             magresMetadataSchema,
                             magresVersionSchema)


class MagresDB(object):

    def __init__(self, dbname='ccpnc'):

        self.config = Config()
        self.client = MongoClient(host=self.config.db_url,
                                  port=self.config.db_port)
        ccpnc = self.client[dbname]

        # Grab the collections
        # 1. GridFS collection for magres files
        self.magresFilesFS = GridFS(ccpnc, 'magresFilesFS')
        # 2. Metadata collection (one element per database entry,
        # including history)
        self.magresMetadata = ccpnc.magresMetadata
        # 3. Searchable data, updated when the other two change, to the latest
        # version
        self.magresIndex = ccpnc.magresIndex

        # 4. Unique ID counter
        self.magresIDcount = ccpnc.magresIDcount
        # 5. Logger
        self.magresLog = ccpnc.magresLog

    def addRecord(self, mfile, record_data, version_data):

        # Read in magres file
        magres = readMagres(mfile)

        # Validate data
        data.update({'version_history': []})
        data = magresMetadataSchema.validate(data)

    def generateID(self):        
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
