#!/usr/bin/env python

import os
import sys
import unittest
import functools
import numpy as np
import subprocess as sp
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


def clean_db(method):
    @functools.wraps(method)
    def clean_method(self):
        # Start with a clean database
        self.mdb.client.drop_database('ccpnc-test')
        return method(self)

    return clean_method


class MagresDBTest(unittest.TestCase):

    @mongomock.patch("mongodb://localhost:27017", on_new="pymongo")
    def setUp(self):

        # from tests.py.gridfs_patch import enable_gridfs_integration
        enable_gridfs_integration()
        
        from ccpncdb.config import Config
        from ccpncdb.magresdb import MagresDB
        from ccpncdb.utils import read_magres_file

        config = Config()
        client = config.client()

        self.mdb = MagresDB(client, 'ccpnc-test')
        with open(os.path.join(data_path, 'ethanol.magres')) as f:
            self.eth = read_magres_file(f)

    @mongomock.patch("mongodb://localhost:27017", on_new="pymongo")
    @clean_db
    def testAddRecord(self):
        from ccpncdb.magresdb import MagresDBError

        with open(os.path.join(data_path, 'ethanol.magres')) as f:
            # This should work
            res = self.mdb.add_record(f, _fake_rdata, _fake_vdata)
            self.assertTrue(res.successful)
            self.assertEqual(res.mdbref, '0000001')

        with open(os.path.join(data_path, 'ethanol.magres')) as f:
            # This should not
            with self.assertRaises(MagresDBError):
                self.mdb.add_record(f, {}, {})

        # Test getting the record back
        rec = self.mdb.get_record(res.id)
        self.assertEqual(rec['immutable_id'], res.mdbref)

        with self.assertRaises(MagresDBError):
            self.mdb.get_record('Invalid ID')

        with self.assertRaises(MagresDBError):
            self.mdb.get_record('0'*24)

    @mongomock.patch("mongodb://localhost:27017", on_new="pymongo")
    @clean_db
    def testAddArchive(self):
        from ccpncdb.magresdb import MagresDBError

        with open(os.path.join(data_path, 'test.csv.zip'), 'rb') as a:
            results = self.mdb.add_archive(a, _fake_rdata, _fake_vdata)

        self.assertEqual(len(results), 2)

        names = []
        for name, res in results.items():
            rec = self.mdb.magresIndex.find_one({'_id': ObjectId(res.id)})
            names.append(rec['chemname'])

        self.assertEqual(sorted(names), ['alanine', 'ethanol'])

        with open(os.path.join(data_path, 'broken.zip'), 'rb') as a:
            with self.assertRaises(MagresDBError):
                results = self.mdb.add_archive(a, _fake_rdata, _fake_vdata)

        # Check that there is no file that was actually added
        for rec in self.mdb.magresIndex.find({}):
            self.assertTrue('broken' not in rec['chemname'])

    @mongomock.patch("mongodb://localhost:27017", on_new="pymongo")
    @clean_db
    def testAddVersion(self):

        r_id = None
        with open(os.path.join(data_path, 'ethanol.fake.magres')) as f:
            res = self.mdb.add_record(f, _fake_rdata, _fake_vdata)
            r_id = res.id

        # Now add a new version
        with open(os.path.join(data_path, 'ethanol.magres')) as f:
            self.mdb.add_version(r_id, f, _fake_vdata)

            rec = self.mdb.get_record(r_id)

            msiso = MSIsotropy.get(self.eth['Atoms'])

            for data in rec['nmrdata']:
                el = data['species']
                ms = data['ms']
                ms = [np.average(list(T.values())) for T in ms]

                inds = AtomSelection.from_element(self.eth['Atoms'],
                                                  el).indices

                self.assertTrue(np.isclose(np.sort(ms),
                                           np.sort(msiso[inds])).all())

            self.assertEqual(rec['version_count'], 2)

        # And now try what happens when you add a new version with no magres
        # file - just metadata
        vdata = {
            'license': 'odc-by'
        }
        self.mdb.add_version(r_id, version_data=vdata)

        rec = self.mdb.get_record(r_id)

        self.assertEqual(rec['last_version']['license'], 'odc-by')

    @mongomock.patch("mongodb://localhost:27017", on_new="pymongo")
    @clean_db
    def testGetFile(self):

        with open(os.path.join(data_path, 'ethanol.magres')) as f:
            fstr = f.read()
            # This should work
            res = self.mdb.add_record(fstr, _fake_rdata, _fake_vdata)
            # Get record
            rec = self.mdb.magresIndex.find_one({'_id': ObjectId(res.id)})
            print(rec)  # Debugging print statement
            # Get file id
            fs_id = rec['version_history'][-1]['magresFilesID']
            print("File ID:", fs_id)  # Debugging print statement

            # Ensure fs_id is not None
            if fs_id is None:
                raise ValueError("fs_id is None, check add_record method and version_history")

            fstr2 = self.mdb.get_magres_file(fs_id, True)

            self.assertEqual(fstr, fstr2)

    @mongomock.patch("mongodb://localhost:27017", on_new="pymongo")
    @clean_db
    def testSearch(self):

        ethstr = None
        with open(os.path.join(data_path, 'ethanol.magres')) as f:
            ethstr = f.read()

        alastr = None
        with open(os.path.join(data_path, 'alanine.magres')) as f:
            alastr = f.read()

        # Add it twice
        rdata_1 = dict(_fake_rdata)
        rdata_1['chemname'] = 'ethanol'
        res_1 = self.mdb.add_record(ethstr, rdata_1, _fake_vdata)

        rdata_2 = dict(_fake_rdata)
        rdata_2['chemname'] = 'ethyl alcohol'
        res_2 = self.mdb.add_record(ethstr, rdata_2, _fake_vdata)

        rdata_3 = dict(_fake_rdata)
        rdata_3['chemname'] = 'alanine'
        vdata_3 = dict(_fake_vdata)
        vdata_3['license'] = 'pddl'
        vdata_3['doi'] = '10.1010/ABCD123456'
        res_3 = self.mdb.add_record(alastr, rdata_3, vdata_3)

        #Test search by chemname
        found = self.mdb.search_record([{
            'type': 'chemname',
            'args': {'pattern': '"Ethanol"'},
            'negate_query': False
        }])
        found = list(found)

        self.assertEqual(len(found), 1)
        self.assertEqual(str(found[0]['_id']), res_1.id)
        
        #Test search by doi
        #DOI perfect string match, all caps
        found = self.mdb.search_record([{
            'type': 'doi',
            'args': {'doi': '10.1010/ABCD123456'},
            'negate_query': False
            }])
        found = list(found)
        self.assertEqual(len(found), 1)
        self.assertEqual(str(found[0]['_id']), res_3.id)

        #Now a negated DOI search - perfect string match, all caps
        found = self.mdb.search_record([{
            'type': 'doi',
            'args': {'doi': '10.1010/ABCD123456'},
            'negate_query': True
            }])
        found = list(found)
        self.assertEqual(len(found), 2) #search should return res_1 and res_2
        self.assertEqual(str(found[0]['_id']), res_1.id)
        self.assertEqual(str(found[1]['_id']), res_2.id)
        
        #DOI perfect string match, lowercase letters
        found = self.mdb.search_record([{
            'type': 'doi',
            'args': {'doi': '10.1010/abcd123456'},
            'negate_query': False
            }])
        found = list(found)
        self.assertEqual(len(found), 1)
        self.assertEqual(str(found[0]['_id']), res_3.id)

        #Now a negated DOI search - perfect string match, lowercase letters
        found = self.mdb.search_record([{
            'type': 'doi',
            'args': {'doi': '10.1010/abcd123456'},
            'negate_query': True
            }])
        found = list(found)
        self.assertEqual(len(found), 2) #search should return res_1 and res_2, same as for uppercase
        self.assertEqual(str(found[0]['_id']), res_1.id) #should produce same result as for uppercase
        self.assertEqual(str(found[1]['_id']), res_2.id) #should produce same result as for uppercase
        
        #DOI wrong characters on purpose this should return zero results
        found = self.mdb.search_record([{
            'type': 'doi',
            'args': {'doi': '10.1010/abcd123498'},
            'negate_query': False
            }])
        found = list(found)
        self.assertEqual(len(found), 0)

        #Now a negated DOI search with wrong characters on purpose this should return all results
        found = self.mdb.search_record([{
            'type': 'doi',
            'args': {'doi': '10.1010/abcd123498'},
            'negate_query': True
            }])
        found = list(found)
        self.assertEqual(len(found), 3) #search should return res_1, res_2 and res_3
        
        #DOI wildcard search - prefix
        found = self.mdb.search_record([{
            'type': 'doi',
            'args': {'doi': '10.1010/*'},
            'negate_query': False
            }])
        found = list(found)
        self.assertEqual(len(found), 1)
        self.assertEqual(str(found[0]['_id']), res_3.id)

        #Negated DOI wildcard search - prefix
        found = self.mdb.search_record([{
            'type': 'doi',
            'args': {'doi': '10.1010/*'},
            'negate_query': True
            }])
        found = list(found)
        self.assertEqual(len(found), 2) #search should return res_1 and res_2
        
        #DOI wildcard search - suffix
        found = self.mdb.search_record([{
            'type': 'doi',
            'args': {'doi': '*/ABCD123456'},
            'negate_query': False
            }])
        found = list(found)
        self.assertEqual(len(found), 1)
        self.assertEqual(str(found[0]['_id']), res_3.id)

        #Negated DOI wildcard search - suffix
        found = self.mdb.search_record([{
            'type': 'doi',
            'args': {'doi': '*/ABCD123456'},
            'negate_query': True
            }])
        found = list(found)
        self.assertEqual(len(found), 2) #search should return res_1 and res_2
        
        #DOI wildcard search - central characters of doi
        found = self.mdb.search_record([{
            'type': 'doi',
            'args': {'doi': '*1010/ABCD*'},
            'negate_query': False
            }])
        found = list(found)
        self.assertEqual(len(found), 1)
        self.assertEqual(str(found[0]['_id']), res_3.id)

        #Negated DOI wildcard search - central characters of doi
        found = self.mdb.search_record([{
            'type': 'doi',
            'args': {'doi': '*1010/ABCD*'},
            'negate_query': True
            }])
        found = list(found)
        self.assertEqual(len(found), 2) #search should return res_1 and res_2

        # Test search using tokens
        found = self.mdb.search_record([{
            'type': 'chemname',
            'args': {'pattern': 'alcohol ethyl'},
            'negate_query': False
        }])
        found = list(found)

        self.assertEqual(len(found), 1)
        self.assertEqual(str(found[0]['_id']), res_2.id)

        # Test by mdbref
        found = self.mdb.search_record([{
            'type': 'mdbref',
            'args': {'mdbref': '0000002'},
            'negate_query': False
        }])
        found = list(found)

        self.assertEqual(len(found), 1)
        self.assertEqual(str(found[0]['_id']), res_2.id)

        # Test by formula
        found = self.mdb.search_record([{
            'type': 'formula',
            'args': {'formula': 'C2H6O', 'subset': False},
            'negate_query': False
        }])
        found = list(found)

        self.assertEqual(len(found), 2)

        # Try with subset
        found = self.mdb.search_record([{
            'type': 'formula',
            'args': {'formula': 'N4', 'subset': True},
            'negate_query': False
        }])
        found = list(found)

        self.assertEqual(len(found), 1)

        # Now try obfuscating one
        self.mdb.edit_record(res_1.id, {'$set': {'visible': False}})

        # Test by license
        found = self.mdb.search_record([{
            'type': 'license',
            'args': {'license': 'cc-by'},
            'negate_query': False
        }])
        found = list(found)

        self.assertEqual(len(found), 1)
        self.assertEqual(str(found[0]['_id']), res_2.id)

        # Negated search for license
        found = self.mdb.search_record([{
            'type': 'license',
            'args': {'license': 'cc-by'},
            'negate_query': True
        }])
        found = list(found)

        self.assertEqual(len(found), 1) # there is one record with 'pddl' license which should be returned
        self.assertEqual(str(found[0]['_id']), res_3.id) # the returned rcord should be res_3

        # Test by MS

        if isinstance(self.mdb.client, mongomock.MongoClient):
            import warnings
            warnings.warn("MongoDB mock does not support this search, skipping test case")
        else:
            found = self.mdb.search_record([{
                'type': 'msRange',
                'args': {'sp': 'N', 'minms': 100.0, 'maxms': 200.0},
                'negate_query': False
            }])
            found = list(found)

            self.assertEqual(len(found), 1)
            self.assertEqual(found[0]['chemname'], 'alanine')

        # External reference
        vdata = dict(_fake_vdata)
        vdata['extref_type'] = 'csd'
        vdata['extref_code'] = 'ABC123'
        self.mdb.add_record(alastr, rdata_3, vdata)
        vdata['extref_code'] = 'ABC456'
        self.mdb.add_record(alastr, rdata_3, vdata)

        # Search only by type
        found = self.mdb.search_record([{
            'type': 'extref',
            'args': {'reftype': 'csd', 'other_reftype': None, 'refcode': None},
            'negate_query': False
        }])
        found = list(found)

        self.assertEqual(len(found), 2)

        # Negated search for reftype only - reftype csd
        found = self.mdb.search_record([{
            'type': 'extref',
            'args': {'reftype': 'csd', 'other_reftype': None, 'refcode': None},
            'negate_query': True
        }])
        found = list(found)
        self.assertEqual(len(found), 0) # No other records should be returned

        # Negated search for reftype only - reftype icsd
        found = self.mdb.search_record([{
            'type': 'extref',
            'args': {'reftype': 'icsd', 'other_reftype': None, 'refcode': None},
            'negate_query': True
        }])
        found = list(found)
        self.assertEqual(len(found), 2) # Both records with 'csd' reftype should be returned

        # Add code
        found = self.mdb.search_record([{
            'type': 'extref',
            'args': {'reftype': 'csd', 'other_reftype': None, 'refcode': 'ABC123'},
            'negate_query': False
        }])
        found = list(found)

        self.assertEqual(len(found), 1)

        # Negated search for code
        found = self.mdb.search_record([{
            'type': 'extref',
            'args': {'reftype': 'csd', 'other_reftype': None, 'refcode': 'ABC123'},
            'negate_query': True
        }])
        found = list(found)
        self.assertEqual(len(found), 1) # One record where refcode is 'ABC456' should be returned
        self.assertEqual(str(found[0]['last_version']['extref_code']), 'ABC456') #verfiy that the returned record's refcode is indeed 'ABC456'

    @mongomock.patch("mongodb://localhost:27017", on_new="pymongo")
    @clean_db
    def testUniqueID(self):

        self.assertEqual(self.mdb.generate_id(), '0000001')
        self.assertEqual(self.mdb.generate_id(), '0000002')
        self.assertEqual(self.mdb.generate_id(), '0000003')


if __name__ == '__main__':

    ps = sp.Popen(['ps', '-all'], stdout=sp.PIPE, stderr=sp.PIPE)

    stdout, stderr = ps.communicate()
    if b'mongod' not in stdout.split():
        raise RuntimeError('Please run an instance of mongod in another shell'
                           ' for testing')

    unittest.main()
