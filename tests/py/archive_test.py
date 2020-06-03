#!/usr/bin/env python

import os
import sys
import unittest

file_path = os.path.split(__file__)[0]
data_path = os.path.join(file_path, '../data')
sys.path.append(os.path.abspath(os.path.join(file_path, '../../')))


class ArchiveTest(unittest.TestCase):

    def testZip(self):
        from ccpncdb.archive import MagresArchive

        with open(os.path.join(data_path, 'test.zip'), 'rb') as a:
            archive = MagresArchive(a)
            names = []
            for f in archive.files():
                names.append(f.name)

            self.assertEqual(names, ['alanine.magres', 'ethanol.magres'])

    def testCsvZip(self):
        from ccpncdb.archive import MagresArchive

        with open(os.path.join(data_path, 'test.csv.zip'), 'rb') as a:
            archive = MagresArchive(a, version_data={'doi': '000'})
            doi = {}
            for f in archive.files():
                doi[f.name] = f.version_data['doi']

            self.assertEqual(doi['ethanol.magres'], '000')
            self.assertEqual(doi['alanine.magres'], '111')

    def testTar(self):
        from ccpncdb.archive import MagresArchive

        with open(os.path.join(data_path, 'test.tar'), 'rb') as a:
            archive = MagresArchive(a)
            names = []
            for f in archive.files():
                names.append(f.name)

            self.assertEqual(names, ['alanine.magres', 'ethanol.magres'])

    def testWriteZip(self):
        from ccpncdb.archive import MagresArchive

        testfile = os.path.join(data_path, 'test_write.zip')
        fnames = ['ethanol.magres', 'alanine.magres']

        with open(testfile, 'wb') as a:

            archive = MagresArchive(a, mode='w')

            vdata = {
                'alanine': {
                    'doi': '111'
                }
            }

            for fname in fnames:
                with open(os.path.join(data_path, fname)) as f:
                    chemname = fname.split('.')[0]
                    archive.add_file(fname, f.read(),
                                     record_data={'chemname': chemname}, 
                                     version_data=vdata.get(chemname, {}))

            archive.write()

        # Test re-reading the file
        with open(testfile, 'rb') as a:
            archive = MagresArchive(a)

            for f in archive.files():

                chemname = f.name.split('.')[0]

                self.assertTrue(f.name in fnames)
                self.assertEqual(f.record_data, {'chemname': chemname})
                self.assertEqual(f.version_data, vdata.get(chemname, {}))

        # Delete the file
        os.remove(testfile)

if __name__ == "__main__":

    unittest.main()
