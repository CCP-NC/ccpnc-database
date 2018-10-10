#!/usr/bin/env python

# Testing the indexing functions used to pre-process the files to upload

import os
import sys
import json
import time
import unittest

file_path = os.path.split(__file__)[0]
data_path = os.path.join(file_path, '../data')
sys.path.append(os.path.abspath(os.path.join(file_path, '../../')))

from ase import io
from db_indexing import (_prime_factors, getFormula, getMSMetadata,
                         getStochiometry, getMolecules)


class IndexingTest(unittest.TestCase):

    def testPrimeFactors(self):
        facs = _prime_factors(6)
        self.assertEqual(facs, [2, 3])
        facs = _prime_factors(21)
        self.assertEqual(facs, [3, 7])

    def testFormula(self):
        eth = io.read(os.path.join(data_path, 'ethanol.magres'))
        f = getFormula(eth)
        targ_f = [
            {'species': 'C', 'n': 2},
            {'species': 'H', 'n': 6},
            {'species': 'O', 'n': 1}
        ]
        self.assertEqual(f, targ_f)

    def testStochiometry(self):
        ala = io.read(os.path.join(data_path, 'alanine.magres'))
        f = getFormula(ala)
        s = getStochiometry(f)
        self.assertEqual(s[2]['n'], 1) # Nitrogen

    def testMolecules(self):
        ala = io.read(os.path.join(data_path, 'alanine.magres'))
        m = getMolecules(ala)
        print(m)

    def testMS(self):
        eth = io.read(os.path.join(data_path, 'ethanol.magres'))
        ms = getMSMetadata(eth)
        # Test the only oxygen one...
        self.assertAlmostEqual(ms[2]['iso'][0], 267.0122765992025)


if __name__ == '__main__':

    unittest.main()
