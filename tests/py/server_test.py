#!/usr/bin/env python

import os
import sys
import json
import unittest
import numpy as np
import subprocess as sp

from io import BytesIO
from hashlib import md5
from bson.objectid import ObjectId
from soprano.selection import AtomSelection
from soprano.properties.nmr import MSIsotropy

import mongomock
from mongomock.gridfs import enable_gridfs_integration

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
    'user_name': 'John Smith'
}

_fake_vdata = {
    'license': 'cc-by',
}

_fake_user = {
    '_auth_id': _fake_orcid['path'],
    '_auth_tk': 'XXX'
}


class MDBServerTest(unittest.TestCase):

    @mongomock.patch("mongodb://localhost:27017", on_new="create")
    def setUp(self):
        enable_gridfs_integration()

        from ccpncdb.server import MainServer
        from ccpncdb.utils import read_magres_file
        from ccpncdb.orcid import FakeOrcidConnection

        self.serv = MainServer(path=os.path.join(file_path, '../serv'))
        # Set up a fake connection
        orcid = FakeOrcidConnection()
        orcid.request_tokens('123456')
        self.serv.orcid = orcid

        with open(os.path.join(data_path, 'ethanol.magres')) as f:
            self.eth = read_magres_file(f)

        self.client = self.serv.app.test_client()

    @mongomock.patch("mongodb://localhost:27017", on_new="create")
    def testStatic(self):

        @self.serv.app.route('/')
        def root():
            return self.serv.send_static('index.html')

        resp = self.client.get('/')
        html = next(resp.response).decode('utf-8')

        with open(os.path.join(file_path, '../serv/static/index.html')) as f:
            self.assertEqual(html, f.read())
        self.assertEqual(resp.headers['Content-Type'],
                        'text/html; charset=utf-8')

        resp.close()

    @mongomock.patch("mongodb://localhost:27017", on_new="create")
    def testUserInfo(self):

        @self.serv.app.route('/uinfo', methods=['POST'])
        def uinfo():
            rinfo = self.serv.request_user_info()
            return str(rinfo), self.serv.HTTP_200_OK

        resp = self.client.post('/uinfo', data=_fake_user)

        self.assertEqual(resp.status_code, 200)

    @mongomock.patch("mongodb://localhost:27017", on_new="create")
    def testMagres(self):

        from ccpncdb.schemas import csvProperties

        @self.serv.app.route('/upload', methods=['POST'])
        def upload():
            return self.serv.upload_record()

        @self.serv.app.route('/get_record', methods=['GET'])
        def get_record():
            return self.serv.get_record()

        @self.serv.app.route('/get_magres', methods=['GET'])
        def get_magres():
            return self.serv.get_magres()

        @self.serv.app.route('/get_csv', methods=['GET'])
        def get_csv():
            return self.serv.get_csv()

        @self.serv.app.route('/get_magres_archive', methods=['GET'])
        def get_magres_archive():
            return self.serv.get_magres_archive()

        updata = dict(_fake_user)
        updata.update(_fake_rdata)
        updata.update(_fake_vdata)
        updata['magres-file'] = (BytesIO(self.eth['string'].encode('utf8')),
                                'ethanol.magres')

        print(updata)

        # First, try to upload
        resp = self.client.post('/upload', data=updata)
        self.assertEqual(resp.status_code, 200)
        mdbref = next(resp.response).decode('utf-8')

        # Retrieve record
        resp = self.client.get('/get_record',
                            json={'mdbref': mdbref})
        self.assertEqual(resp.status_code, 200)
        rec = json.loads(next(resp.response))

        # Finally, the file
        m_id = rec['last_version']['magresFilesID']

        resp = self.client.get('/get_magres',
                            query_string={'magres_id': m_id})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(next(resp.response).decode('utf-8'),
                        self.eth['string'])

        # And the CSV
        resp = self.client.get('/get_csv',
                            query_string={'oid': rec['id'], 'v': 0})
        self.assertEqual(resp.status_code, 200)

        lines = [r.decode('utf-8').strip() for r in resp.response]

        _fake_alldata = dict(_fake_rdata, **_fake_vdata)
        self.assertEqual(lines[0], ','.join(csvProperties))
        self.assertEqual(lines[1], ','.join([_fake_alldata.get(p, '')
                                            for p in csvProperties]))


if __name__ == '__main__':

    ps = sp.Popen(['ps', '-all'], stdout=sp.PIPE, stderr=sp.PIPE)

    #stdout, stderr = ps.communicate()
    #if b'mongod' not in stdout.split():
    #    raise RuntimeError('Please run an instance of mongod in another shell'
    #                       ' for testing')

    unittest.main()
