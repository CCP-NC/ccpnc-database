#!/usr/bin/env python

import os
import sys
import unittest
import subprocess as sp
from hashlib import md5

file_path = os.path.split(__file__)[0]
data_path = os.path.join(file_path, '../data')
sys.path.append(os.path.abspath(os.path.join(file_path, '../../')))


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
        pass

    @clean_db
    def testUniqueID(self):

        self.assertEqual(self.mdb.generateID(), '0000001')
        self.assertEqual(self.mdb.generateID(), '0000002')
        self.assertEqual(self.mdb.generateID(), '0000003')


if __name__ == '__main__':

    ps = sp.Popen(['ps', '-all'], stdout=sp.PIPE, stderr=sp.PIPE)

    stdout, stderr = ps.communicate()
    if b'mongod' not in stdout.split():
        raise RuntimeError('Please run an instance of mongod in another shell'
                           ' for testing')

    unittest.main()
