import os
import sys
import argparse as ap
from pymongo import MongoClient

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
newdb = MagresDB(client, args.newdb)

# Retrieve all entries in collection Metadata
to_convert = [m for m in olddb.magresMetadata.find({})]
to_convert = sorted(to_convert, key=lambda x: x['version_history'][0]['date'])


def get_new_rdata(entry):
    rdata = {'chemname': entry['chemname'],
             'orcid': entry['orcid']}
    return rdata

for entry in to_convert:
    print(entry)
