#!/usr/bin/env python

import os
import sys
import unittest

file_path = os.path.split(__file__)[0]
data_path = os.path.join(file_path, '../data')
sys.path.append(os.path.abspath(os.path.join(file_path, '../../')))

_fake_orcid = {
    'path': '0000-0000-0000-0000',
    'host': 'none',
    'uri': '0000-0000-0000-0000'
}

class SchemaTest(unittest.TestCase):

    def testRegexp(self):
        
        from ccpncdb.schemas import (orcid_path_re, namestr_re)

        # Acceptable names
        self.assertTrue(namestr_re.match('John Smith-09'))
        self.assertFalse(namestr_re.match('$$$'))

        # ORCIDs
        self.assertTrue(orcid_path_re.match('0123-4567-8901-234X'))
        self.assertFalse(orcid_path_re.match('not an orcid'))     
    
    def testRecordSchema(self):

        from ccpncdb.schemas import (magresRecordSchemaUser, 
                                     magresRecordSchemaAutomatic, 
                                     validate_with)

        rdatau = {
           'chemname': 'Test Compound',
           'orcid': _fake_orcid
        }

        res = validate_with(rdatau, magresRecordSchemaUser)
        self.assertTrue(res.result)

        res = validate_with({}, magresRecordSchemaUser)
        self.assertFalse(res.result)
        self.assertEqual(res.missing, ['chemname', 'orcid'])

        rdatau['chemname'] = '$$'
        res = validate_with(rdatau, magresRecordSchemaUser)
        self.assertFalse(res.result)
        self.assertEqual(res.invalid, 'chemname')



if __name__ == "__main__":

    unittest.main()