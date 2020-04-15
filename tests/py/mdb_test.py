#!/usr/bin/env python

import os
import sys
import unittest
import numpy as np
import subprocess as sp
from hashlib import md5
from bson.objectid import ObjectId
from soprano.selection import AtomSelection
from soprano.properties.nmr import MSIsotropy

file_path = os.path.split(__file__)[0]
data_path = os.path.join(file_path, '../data')
sys.path.append(os.path.abspath(os.path.join(file_path, '../../')))


_fake_orcid = {
    'path': '0000-0000-0000-0000',
    'host': 'none',
    'uri': '0000-0000-0000-0000'
}

_fake_rdata = {
    'chemname': 'ethanol',
    'orcid': _fake_orcid,
    'license': 'cc-by',
    'user_name': 'John Smith',
    'user_institution': 'Academia University',
    'doi': 'N/A'
}


def rndname_gen():
    m = md5()
    m.update(bytes(str(dt.now()), 'UTF-8'))
    return m.hexdigest()


def clean_db(method):
    def clean_method(self):
        # Start with a clean database
        self.mdb.client.drop_database('ccpnc-test')
        return method(self)

    return clean_method


class MagresDBTest(unittest.TestCase):

    def setUp(self):
        from ccpncdb.magresdb import MagresDB
        from ccpncdb.utils import read_magres_file

        self.mdb = MagresDB('ccpnc-test')
        with open(os.path.join(data_path, 'ethanol.magres')) as f:
            self.eth = read_magres_file(f)

    @clean_db
    def testAddRecord(self):
        from ccpncdb.magresdb import MagresDBError

        with open(os.path.join(data_path, 'ethanol.magres')) as f:
            # This should work
            res = self.mdb.add_record(f, _fake_rdata, {})
            self.assertTrue(res.successful)
            self.assertEqual(res.mdbref, '0000001')

        with open(os.path.join(data_path, 'ethanol.magres')) as f:
            # This should not
            with self.assertRaises(MagresDBError):
                self.mdb.add_record(f, {}, {})

    @clean_db
    def testAddArchive(self):

        with open(os.path.join(data_path, 'test.csv.zip'), 'rb') as a:
            self.mdb.add_archive(a, _fake_rdata, {})

    @clean_db
    def testAddVersion(self):

        r_id = None
        with open(os.path.join(data_path, 'ethanol.fake.magres')) as f:
            res = self.mdb.add_record(f, _fake_rdata, {})
            r_id = res.id

        # Now add a new version
        with open(os.path.join(data_path, 'ethanol.magres')) as f:
            self.mdb.add_version(f, r_id, {}, True)

            rec = self.mdb.magresIndex.find_one({'_id': ObjectId(r_id)})

            msiso = MSIsotropy.get(self.eth['Atoms'])

            for data in rec['nmrdata']:
                el = data['species']
                ms = data['msiso']

                inds = AtomSelection.from_element(self.eth['Atoms'],
                                                  el).indices

                self.assertTrue(np.isclose(np.sort(ms),
                                           np.sort(msiso[inds])).all())

            self.assertEqual(rec['version_count'], 2)

    @clean_db
    def testGetFile(self):

        with open(os.path.join(data_path, 'ethanol.magres')) as f:
            fstr = f.read()
            # This should work
            res = self.mdb.add_record(fstr, _fake_rdata, {})
            # Get record
            rec = self.mdb.magresIndex.find_one({'_id': ObjectId(res.id)})
            # Get file id
            fs_id = rec['version_history'][-1]['magresFilesID']

            fstr2 = self.mdb.get_magres_file(fs_id, True)

            self.assertEqual(fstr, fstr2)

    @clean_db
    def testUniqueID(self):

        self.assertEqual(self.mdb.generate_id(), '0000001')
        self.assertEqual(self.mdb.generate_id(), '0000002')
        self.assertEqual(self.mdb.generate_id(), '0000003')


if __name__ == '__main__':

    ps = sp.Popen(['ps', '-all'], stdout=sp.PIPE, stderr=sp.PIPE)

    stdout, stderr = ps.communicate()
    if b'mongod' not in stdout.split():
        raise RuntimeError('Please run an instance of mongod in another shell'
                           ' for testing')

    unittest.main()
