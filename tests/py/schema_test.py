#!/usr/bin/env python

import os
import sys
import unittest

file_path = os.path.split(__file__)[0]
data_path = os.path.join(file_path, '../data')
sys.path.append(os.path.abspath(os.path.join(file_path, '../../')))

class SchemaTest(unittest.TestCase):

    def testRegexp(self):
        
        from ccpncdb.schemas import (orcid_path_re, namestr_re)

        # Acceptable names
        self.assertTrue(namestr_re.match('John Smith-09'))
        self.assertFalse(namestr_re.match('$$$'))

        # ORCIDs
        self.assertTrue(orcid_path_re.match('0123-4567-8901-234X'))
        self.assertFalse(orcid_path_re.match('not an orcid'))        
        

if __name__ == "__main__":

    unittest.main()