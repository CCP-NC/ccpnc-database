#!/usr/bin/env python

# Testing the Python app for the database (uploading, deleting, etc.)

import os
import sys
import json
import time
import unittest
import subprocess as sp
from datetime import datetime as dt

file_path = os.path.split(__file__)[0]
data_path = os.path.join(file_path, '../data')
sys.path.append(os.path.abspath(os.path.join(file_path, '../../')))

import main as ccpnc_db
from orcid import FakeOrcidConnection
from db_schema import magresVersionOptionals
from db_interface import (addMagresFile, addMagresArchive, editMagresFile,
                          getMagresFile, databaseSearch, removeMagresFiles)
from db_indexing import (getFormula, getMSMetadata)


try:
    # Python 2 version
    import md5
    def rndname_gen():
        m = md5.new()
        m.update(str(dt.now()))
        return m.hexdigest()
except ImportError:
    # Python 3 version
    from hashlib import md5
    def rndname_gen():
        m = md5()
        m.update(bytes(str(dt.now()), 'UTF-8'))
        return m.hexdigest()



class CCPNCDBTest(unittest.TestCase):

    def setUp(self):
        ccpnc_db.app.testing = True
        ccpnc_db.app.extensions['orcidlink'] = FakeOrcidConnection()
        self.app = ccpnc_db.app.test_client()

    def testCSV(self):

        csvresp = self.app.get('/csvtemplate')
        header = next(csvresp.response).decode('UTF-8')
        self.assertEqual(header, 'filename,chemname,chemform,' +
                         ','.join(magresVersionOptionals.keys()))

    def testTokens(self):

        tokresp = self.app.get('/gettokens/123456')
        details = json.loads(next(tokresp.response).decode('UTF-8'))
        self.assertEqual(details['orcid'], '0000-0000-0000-0000')
        tokresp = self.app.get('/gettokens/')
        details_cookie = json.loads(next(tokresp.response).decode('UTF-8'))
        # Are they the same?
        self.assertEqual(details['name'], details_cookie['name'])
        # Now delete
        self.app.get('/logout')
        # They shouldn't be around any more
        tokresp = self.app.get('/gettokens/')
        details_cookie = json.loads(next(tokresp.response).decode('UTF-8'))
        self.assertIsNone(details_cookie)

    def testAddMagres(self):

        # Load a file as string
        with open(os.path.join(data_path, 'ethanol.magres')) as magres:
            orcid = {
                'path': '0000-0000-0000-0000',
                'host': 'none',
                'uri': '0000-0000-0000-0000'
            }

            # Add it
            rndname = rndname_gen()
            ind_id = addMagresFile(magres, rndname, orcid)
            self.assertTrue(ind_id)
            # Now remove it
            removeMagresFiles(ind_id)

    def testAddArchive(self):

        testarchives = ['test.tar', 'test.zip']
        orcid = {
            'path': '0000-0000-0000-0000',
            'host': 'none',
            'uri': '0000-0000-0000-0000'
        }

        for archf in testarchives:
            with open(os.path.join(data_path, archf), 'rb') as archive:

                rndname = rndname_gen()

                succ, all_inds = addMagresArchive(archive, rndname, orcid)
                self.assertEqual(succ, 0)

                results = json.loads(databaseSearch([{'type': 'cname',
                                                    'args': {
                                                        'pattern': rndname
                                                    }}]))
                self.assertEqual(len(results), 2)

                # Now delete them
                for r in results:
                    removeMagresFiles(r['index_id'])

        # Now test for the one with a CSV inside
        with open(os.path.join(data_path, 'test.csv.zip'), 'rb') as archive:

            rndname = rndname_gen()

            succ, all_inds = addMagresArchive(archive, rndname, orcid,
                                            data={'doi': '222'})
            self.assertEqual(succ, 0)

            results = json.loads(databaseSearch([{'type': 'cname',
                                                'args': {
                                                    'pattern': rndname
                                                }}]))
            dois = ','.join(sorted([r['version_history'][0]['doi']
                                    for r in results]))
            self.assertEqual(dois, '111,222')
            self.assertEqual(len(results), 2)

            # Now delete them
            for r in results:
                removeMagresFiles(r['index_id'])

    def testAddMagresApp(self):

        try:
            from StringIO import StringIO as sio
        except ImportError:
            from io import StringIO as sio

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
        rndname = rndname_gen()
        with open(os.path.join(data_path, 'ethanol.magres'), 'r') as magres:
            resp = self.app.post('/upload',
                                content_type='multipart/form-data',
                                data={
                                    'orcid': '0000-0000-0000-0000',
                                    'access_token': 'XXX',
                                    'chemname': rndname,
                                    'magres-file': (magres,
                                                    'ethanol.magres')}
                                )
        self.assertEqual(resp._status_code, 200)

        # Now remove it
        results = json.loads(databaseSearch([{'type': 'cname',
                                              'args': {
                                                  'pattern': rndname
                                              }}]))
        ind_id = results[0]['index_id']
        removeMagresFiles(ind_id)

    def testAddArchiveApp(self):

        # "Log in"
        self.app.get('/gettokens/123456')

        with open(os.path.join(data_path, 'test.tar'), 'rb') as archive:

            rndname = rndname_gen()
            resp = self.app.post('/upload', data={
                'orcid': '0000-0000-0000-0000',
                'access_token': 'XXX',
                'chemname': rndname,
                'magres-file': archive,
                'upload_multi': 'true'}
            )

            self.assertEqual(resp._status_code, 200)

            results = json.loads(databaseSearch([{'type': 'cname',
                                                'args': {
                                                    'pattern': rndname
                                                }}]))
        self.assertEqual(len(results), 2)

        # Now delete them
        for r in results:
            removeMagresFiles(r['index_id'])


if __name__ == '__main__':

    ps = sp.Popen(['ps', '-all'], stdout=sp.PIPE, stderr=sp.PIPE)

    stdout, stderr = ps.communicate()
    if b'mongod' not in stdout.split():
        raise RuntimeError('Please run an instance of mongod in another shell'
                           ' for testing')

    unittest.main()
