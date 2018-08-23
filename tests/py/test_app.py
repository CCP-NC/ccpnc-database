#!/usr/bin/env python

import md5
import sys
import json
import time
import unittest
import subprocess as sp
from datetime import datetime as dt
sys.path.append('../../')

import main as ccpnc_db
from orcid import FakeOrcidConnection
from db_schema import magresVersionOptionals
from db_interface import (addMagresFile, addMagresArchive, editMagresFile,
                          getMagresFile, databaseSearch, removeMagresFiles)
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

    def testAddMagres(self):

        # Load a file as string
        magres = open('../data/ethanol.magres').read()
        orcid = {
            'path': '0000-0000-0000-0000',
            'host': 'none',
            'uri': '0000-0000-0000-0000'
        }

        # Add it
        m = md5.new()
        m.update(str(dt.now()))
        rndname = m.hexdigest()
        ind_id = addMagresFile(magres, rndname, orcid)
        self.assertTrue(ind_id)
        # Now remove it
        removeMagresFiles(ind_id)

    def testAddMagresApp(self):

        # Load a file as string
        magres = open('../data/ethanol.magres').read()
        # "Log in"
        self.app.get('/gettokens/123456')

        # Post file

        # Test 1: fail authentication
        resp = self.app.post('/upload', data={
            'orcid': '0000-0000-0000-0000',
            'access_token': 'XXY'}
        )
        self.assertEqual(resp._status_code, 401)
        # Test 2: fail for lack of file
        resp = self.app.post('/upload', data={
            'orcid': '0000-0000-0000-0000',
            'access_token': 'XXX'}
        )
        self.assertEqual(resp._status_code, 500)
        # Test 3: succeed
        m = md5.new()
        m.update(str(dt.now()))
        rndname = m.hexdigest()
        resp = self.app.post('/upload', data={
            'orcid': '0000-0000-0000-0000',
            'access_token': 'XXX',
            'chemname': rndname,
            'magres': magres}
        )
        self.assertEqual(resp._status_code, 200)

        # Now remove it
        results = json.loads(databaseSearch([{'type': 'cname',
                                              'args': {
                                                  'pattern': rndname
                                              }}]))
        ind_id = results[0]['index_id']
        removeMagresFiles(ind_id)


if __name__ == '__main__':

    ps = sp.Popen(['ps', '-all'], stdout=sp.PIPE, stderr=sp.PIPE)

    stdout, stderr = ps.communicate()
    if 'mongod' not in stdout.split():
        raise RuntimeError('Please run an instance of mongod in another shell'
                           ' for testing')

    unittest.main()
