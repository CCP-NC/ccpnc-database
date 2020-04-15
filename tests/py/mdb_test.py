#!/usr/bin/env python

import os
import sys
import unittest
import subprocess as sp
from hashlib import md5

file_path = os.path.split(__file__)[0]
data_path = os.path.join(file_path, '../data')
sys.path.append(os.path.abspath(os.path.join(file_path, '../../')))


_fake_orcid = {
    'path': '0000-0000-0000-0000',
    'host': 'none',
    'uri': '0000-0000-0000-0000'
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
        self.mdb = MagresDB('ccpnc-test')

    @clean_db
    def testAddRecord(self):
        from ccpncdb.magresdb import MagresDBError

        rdata = {
            'chemname': 'ethanol',
            'orcid': _fake_orcid,
            'license': 'cc-by',
            'user_name': 'John Smith',
            'user_institution': 'Academia University',
            'doi': 'N/A'
        }

        with open(os.path.join(data_path, 'ethanol.magres')) as f:
            # This should work
            res = self.mdb.add_record(f, rdata, {})
            self.assertTrue(res.successful)
            self.assertEqual(res.mdbref, '0000001')

        with open(os.path.join(data_path, 'ethanol.magres')) as f:
            # This should not
            with self.assertRaises(MagresDBError):
                self.mdb.add_record(f, {}, {})

    @clean_db
    def testAddArchive(self):

        rdata = {
            'chemname': 'ethanol',
            'orcid': _fake_orcid,
            'license': 'cc-by',
            'user_name': 'John Smith',
            'user_institution': 'Academia University',
            'doi': 'N/A'
        }

        with open(os.path.join(data_path, 'test.csv.zip'), 'rb') as a:
            self.mdb.add_archive(a, rdata, {})

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
