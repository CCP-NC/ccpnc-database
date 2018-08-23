#!/usr/bin/env python

import sys
import json
import time
import unittest
import subprocess as sp
sys.path.append('../../')

import main as ccpnc_db
from orcid import FakeOrcidConnection
from db_schema import magresVersionOptionals
# Launch app


class CCPNCDBTest(unittest.TestCase):

    def setUp(self):
        ccpnc_db.app.testing = True
        ccpnc_db.app.extensions['orcidlink'] = FakeOrcidConnection()
        self.app = ccpnc_db.app.test_client()

    def testCSV(self):

        csvresp = self.app.get('/csvtemplate')
        header = csvresp.response.next()
        self.assertEqual(header, 'filename,chemname,chemform,' +
                         ','.join(magresVersionOptionals.keys()))

    def testTokens(self):

        tokresp = self.app.get('/gettokens/123456')
        details = json.loads(tokresp.response.next())
        self.assertEqual(details['orcid'], '0000-0000-0000-0000')
        tokresp = self.app.get('/gettokens/')
        details_cookie = json.loads(tokresp.response.next())
        # Are they the same?
        self.assertEqual(details['name'], details_cookie['name'])
        # Now delete
        self.app.get('/logout')
        # They shouldn't be around any more
        tokresp = self.app.get('/gettokens/')
        details_cookie = json.loads(tokresp.response.next())
        self.assertIsNone(details_cookie)


if __name__ == '__main__':

    ps = sp.Popen(['ps', '-all'], stdout=sp.PIPE, stderr=sp.PIPE)

    stdout, stderr = ps.communicate()
    if 'mongod' not in stdout.split():
        raise RuntimeError('Please run an instance of mongod in another shell'
                           ' for testing')

    unittest.main()
