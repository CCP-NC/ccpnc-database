#!/usr/bin/env python

import os
import sys
import unittest
import numpy as np
import subprocess as sp
from hashlib import md5
from bson.objectid import ObjectId

file_path = os.path.split(__file__)[0]
data_path = os.path.join(file_path, '../data')
sys.path.append(os.path.abspath(os.path.join(file_path, '../../')))

def clean_db(method):
    def clean_method(self):
        # Start with a clean database
        self.logger.client.drop_database('ccpnc-log-test')
        return method(self)

    return clean_method

class LoggerTest(unittest.TestCase):
    
    def setUp(self):
        from ccpncdb.config import Config
        from ccpncdb.log import Logger
    
        config = Config()
        client = config.client()

        self.logger = Logger(client, 'ccpnc-log-test')

    @clean_db
    def testAddLog(self):
        
        # Test adding a single log message
        self.logger.log('LOREM IPSUM', '0000-0000-0000', {'x': 0})

        # Retrieve it
        ans = self.logger.logs.find_one({'x': 0})

        self.assertEqual(ans['message'], 'LOREM IPSUM')


if __name__ == '__main__':

    ps = sp.Popen(['ps', '-all'], stdout=sp.PIPE, stderr=sp.PIPE)

    stdout, stderr = ps.communicate()
    if b'mongod' not in stdout.split():
        raise RuntimeError('Please run an instance of mongod in another shell'
                           ' for testing')

    unittest.main()
