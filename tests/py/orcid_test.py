#!/usr/bin/env python

import os
import sys
import unittest

file_path = os.path.split(__file__)[0]
data_path = os.path.join(file_path, '../data')
sys.path.append(os.path.abspath(os.path.join(file_path, '../../')))

class OrcidTest(unittest.TestCase):

    def setUp(self):

        from ccpncdb.orcid import FakeOrcidConnection

        self.c = FakeOrcidConnection()

    def testConnection(self):

        from ccpncdb.orcid import NoOrcidTokens

        # We test what's possible without actually having a real connection
        with self.assertRaises(NoOrcidTokens):
            self.c.request_tokens('111111')

        # Request with the correct code
        self.c.request_tokens('123456')

        tk = self.c.get_tokens()

        client_info = {'orcid': '0000-0000-0000-0000', 
                       'access_token': 'XXX'}

        self.assertEqual(tk['orcid'], '0000-0000-0000-0000')
        self.assertEqual(tk['access_token'], 'XXX')

        self.assertTrue(self.c.authenticate(client_info))

        info = self.c.request_info(client_info)

        self.assertEqual(info['orcid-identifier']['path'], 
                         client_info['orcid'])


if __name__ == "__main__":

    unittest.main()