import os
import sys
import json
import argparse as ap
from bson.objectid import ObjectId
import pymongo
from gridfs import GridFS, NoFile
from soprano.utils import progbar
from greek import fix_greek

path = os.path.split(__file__)[0]

sys.path.append(os.path.join(path, '..'))

try:
    from ccpncdb.utils import get_name_from_orcid
    from ccpncdb.server import MainServer
    from ccpncdb.magresdb import MagresDB, MagresDBError
except ImportError:
    raise RuntimeError('Script must be located in its original path')

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
parser.add_argument('-noorcid', action='store_true', default=False,
                    help='Do not use ORCID connections to retrieve user names'
                    '(speeds up debug)')

args = parser.parse_args()

# Create client to read old database
client = pymongo.MongoClient(host=args.url, port=args.port)
olddb = client[args.olddb]
mfiles_fs = GridFS(olddb, 'magresFilesFS')
newdb = MagresDB(client, args.newdb)

# Retrieve all entries in collection Metadata
to_convert = [m for m in olddb.magresMetadata.find({})]
to_convert = sorted(to_convert, key=lambda x: x['version_history'][0]['date'])

# Table of users (storing ORCID info) and ORCID connection to retrieve them
if not args.noorcid:
    orcid_users = {}
    orcid_link = MainServer(path=os.path.join(path, '..')).orcid
    pbtoken = orcid_link.request_public_tokens()


def make_new_entry(entry):
    rdata = {'chemname': fix_greek(entry['chemname']),
             'orcid': entry['orcid']}
    version_history = []
    magres_files = []
    dates = []
    # Versions?
    for v in entry['version_history']:

        # Reference?
        csdref = v.get('csd-ref')
        csdnum = v.get('csd-num')

        extref = None
        csd = csdref or csdnum

        vdata = {
            'license': entry['license'],
            'doi': v.get('doi'),
            'extref_type': None,
            'extref_code': None,
            'extref_other': None,
            'chemform': entry['chemform'],
            'notes': v.get('notes')
        }

        if csd is not None:
            vdata['extref_type'] = 'csd'
            vdata['extref_code'] = csd

        version_history.append(vdata)
        m_id = ObjectId(v['magresFilesID'])
        magres_files.append(mfiles_fs.get(m_id))
        dates.append(v['date'])

    return rdata, version_history, magres_files, dates


N = len(to_convert)
print('{0} records found. Starting conversion...'.format(N))

for i, entry in enumerate(to_convert):

    # Progress bar
    sys.stdout.write("\rConverting: {0}".format(progbar(i+1, N)))

    rdata, vhist, mfiles, dates = make_new_entry(entry)

    if not args.noorcid:
        # Retrieve user info
        orcid = rdata['orcid']['path']

        if orcid in orcid_users:
            uinfo = orcid_users[orcid]
        else:
            uinfo = orcid_link.request_public_info(orcid,
                                                   pbtoken['access_token'])
            orcid_users[orcid] = uinfo

        uname = get_name_from_orcid(uinfo)
        rdata['user_name'] = uname

    res = newdb.add_record(mfiles[0], rdata, vhist[0], dates[0])

    for v, mf, d in zip(vhist[1:], mfiles[1:], dates[1:]):
        newdb.add_version(res.id, mf, v, date=d)
