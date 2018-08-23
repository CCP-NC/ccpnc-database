#!/usr/bin/env python

import sys
import unittest
sys.path.append('../../')

import main as ccpnc_db
from db_schema import magresVersionOptionals
# Launch app


class CCPNCDBTest(unittest.TestCase):

    def setUp(self):
        ccpnc_db.app.config['SERVER_NAME'] = 'localhost:8080'
        ccpnc_db.app.testing = True
        self.app = ccpnc_db.app.test_client()

    def testCSV(self):

        csvresp = self.app.get('/csvtemplate')
        header = csvresp.response.next()
        self.assertEqual(header, 'filename,chemname,chemform,' +
                         ','.join(magresVersionOptionals.keys()))

    


if __name__ == '__main__':
    unittest.main()
