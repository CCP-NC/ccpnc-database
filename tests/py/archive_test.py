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
            archive = MagresArchive(a, record_data={'doi': '000'})
            doi = {}
            for f in archive.files():
                doi[f.name] = f.record_data['doi']

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


if __name__ == "__main__":

    unittest.main()