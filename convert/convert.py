import os
import sys
import argparse as ap
from bson.objectid import ObjectId
from pymongo import MongoClient
from gridfs import GridFS, NoFile

path = os.path.split(__file__)[0]

sys.path.append(os.path.join(path, '..'))

from ccpncdb.magresdb import MagresDB

parser = ap.ArgumentParser(description='Convert local database from old'
                           ' to new format')
parser.add_argument('olddb', type=str,
                    help='Name of old database to convert')
parser.add_argument('newdb', type=str,
                    help='Name of new database to convert to')
parser.add_argument('-url', type=str, default='localhost',
                    help='Database URL')
parser.add_argument('-port', type=int, default=27017,
                    help='Database URL')

args = parser.parse_args()

# Create client to read old database
client = MongoClient(host=args.url, port=args.port)
olddb = client[args.olddb]
mfiles_fs = GridFS(olddb, 'magresFilesFS')
newdb = MagresDB(client, args.newdb)

# Retrieve all entries in collection Metadata
to_convert = [m for m in olddb.magresMetadata.find({})]
to_convert = sorted(to_convert, key=lambda x: x['version_history'][0]['date'])



def make_new_entry(entry):
    rdata = {'chemname': entry['chemname'],
             'orcid': entry['orcid']}
    version_history = []
    magres_files = []
    # Versions?
    for v in entry['version_history']:
        vdata = {
            'license': entry['license'],
            'doi': v.get('doi'),
            'extref': None,
            'csd_ref': v.get('csd-ref'),
            'csd_num': v.get('csd-num'),
            'chemform': entry['chemform'],
            'notes': v.get('notes')
        }
        version_history.append(vdata)
        m_id = ObjectId(v['magresFilesID'])
        magres_files.append(mfiles_fs.get(m_id))

    return rdata, version_history, magres_files

for entry in to_convert:
    rdata, vhist, mfiles = make_new_entry(entry)
