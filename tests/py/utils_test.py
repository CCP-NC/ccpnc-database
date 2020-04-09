#!/usr/bin/env python

import os 
import sys
import unittest

file_path = os.path.split(__file__)[0]
data_path = os.path.join(file_path, '../data')
sys.path.append(os.path.abspath(os.path.join(file_path, '../../')))

from ccpncdb.utils import readMagres

class UtilsTest(unittest.TestCase):

    def testReadMagres(self):

        # Test by using an open file
        with open(os.path.join(data_path, 'ethanol.magres')) as f:
            m = readMagres(f)
            self.assertEqual(m.get_chemical_formula(), 'C2H6O')
            self.assertTrue(m.has('ms'))

        # And using a string
        with open(os.path.join(data_path, 'ethanol.magres')) as f:
            m = readMagres(f.read())
            self.assertEqual(m.get_chemical_formula(), 'C2H6O')
            self.assertTrue(m.has('ms'))
    
if __name__ == "__main__":

    unittest.main()