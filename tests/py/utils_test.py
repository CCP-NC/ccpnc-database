#!/usr/bin/env python

import os
import sys
import unittest
import numpy as np
from schema import Schema, And, Optional
from soprano.nmr import NMRTensor

file_path = os.path.split(__file__)[0]
data_path = os.path.join(file_path, '../data')
sys.path.append(os.path.abspath(os.path.join(file_path, '../../')))


class UtilsTest(unittest.TestCase):

    def testReadMagres(self):

        from ccpncdb.utils import read_magres_file

        # Test by using an open file
        with open(os.path.join(data_path, 'ethanol.magres')) as f:
            m = read_magres_file(f)['Atoms']
            self.assertEqual(m.get_chemical_formula(), 'C2H6O')
            self.assertTrue(m.has('ms'))

        # And using a string
        with open(os.path.join(data_path, 'ethanol.magres')) as f:
            mstr = f.read()
            mdata = read_magres_file(mstr)
            m = mdata['Atoms']
            self.assertEqual(m.get_chemical_formula(), 'C2H6O')
            self.assertTrue(m.has('ms'))
            self.assertTrue(mdata['string'], mstr)

    def testPrimeFactors(self):

        from ccpncdb.utils import prime_factors

        self.assertEqual(prime_factors(9), [3, 3])
        self.assertEqual(prime_factors(126), [2, 3, 3, 7])
        self.assertEqual(prime_factors(127), [127])

    def testSchemaKeys(self):

        from ccpncdb.utils import get_schema_keys

        testSchema = Schema({
            'obligatory': str,
            Optional('optional'): str
        })

        self.assertEqual(get_schema_keys(testSchema), ['obligatory',
                                                       'optional'])

    def testFormula(self):

        from ccpncdb.utils import (read_magres_file, extract_formula)

        with open(os.path.join(data_path, 'ethanol.magres')) as f:
            m = read_magres_file(f)['Atoms']
            s = m.get_chemical_symbols()
            self.assertEqual(extract_formula(m), [{'species': 'C', 'n': 2},
                                                  {'species': 'H', 'n': 6},
                                                  {'species': 'O', 'n': 1}])
            self.assertEqual(extract_formula(symbols=s),
                             [{'species': 'C', 'n': 2},
                              {'species': 'H', 'n': 6},
                              {'species': 'O', 'n': 1}])

    def testStochiometry(self):

        from ccpncdb.utils import (read_magres_file, extract_formula,
                                   extract_stochiometry)

        with open(os.path.join(data_path, 'alanine.magres')) as f:
            m = read_magres_file(f)['Atoms']
            formula = extract_formula(m)
            self.assertEqual(extract_stochiometry(formula),
                             [{'species': 'C', 'n': 3},
                              {'species': 'H', 'n': 7},
                              {'species': 'N', 'n': 1},
                              {'species': 'O', 'n': 2}])

    def testMolecules(self):

        from ccpncdb.utils import read_magres_file, extract_molecules

        with open(os.path.join(data_path, 'alanine.magres')) as f:
            m = read_magres_file(f)['Atoms']
            mols = extract_molecules(m)
            for mf in mols:
                self.assertEqual(mf,
                                 [{'species': 'C', 'n': 3},
                                  {'species': 'H', 'n': 7},
                                  {'species': 'N', 'n': 1},
                                  {'species': 'O', 'n': 2}])

    def testNMR(self):

        from ccpncdb.utils import read_magres_file, extract_nmrdata

        with open(os.path.join(data_path, 'ethanol.magres')) as f:
            m = read_magres_file(f)['Atoms']
            symbols = m.get_chemical_symbols()
            ms_tens = [NMRTensor(T, order='h') for T in m.get_array('ms')]
            ms_iso = [T.isotropy for T in ms_tens]
            efg_tens = [NMRTensor(T, order='h') for T in m.get_array('efg')]
            efg_vzz = [T.eigenvalues[2] for T in efg_tens]

            nmrdata = extract_nmrdata(m)
            for eldata in nmrdata:
                for elms in eldata['ms']:
                    iso = np.average(list(elms.values()))
                    i = np.where(np.isclose(ms_iso, iso))[0][0]
                    haeb_evals = [elms[k] for k in ['e_x', 'e_y', 'e_z']]
                    self.assertEqual(symbols[i], eldata['species'])
                    self.assertTrue(np.isclose(haeb_evals,
                                               ms_tens[i].eigenvalues
                                               ).all())

                for elefg in eldata['efg']:
                    vzz = elefg['e_z']
                    i = np.where(np.isclose(efg_vzz, vzz))[0][0]
                    haeb_evals = [elefg[k] for k in ['e_x', 'e_y', 'e_z']]
                    self.assertEqual(symbols[i], eldata['species'])
                    self.assertTrue(np.isclose(haeb_evals,
                                               efg_tens[i].eigenvalues
                                               ).all())

    def testTokenize(self):

        from ccpncdb.utils import tokenize_name

        tname = "3-Ethoxy-2,2-bis(N-oxy-N'-methoxydiazenyl)propan-1-ol"
        tokens = tokenize_name(tname)

        self.assertEqual(tokens, ['ethoxy', 'bis', 'oxy', 'methoxydiazenyl',
                                  'propan', 'ol'])

        tname = ("5,6-Dimethyl-12-hydroxy-1,3,8,10-tetra-azatetracyclo" +
                 "(8.3.2.05,14.06,15)pentadecane-2,4,7,9-tetraone")
        tokens = tokenize_name(tname)

        self.assertEqual(tokens, ['dimethyl', 'hydroxy', 'tetra',
                                  'azatetracyclo', 'pentadecane', 'tetraone'])


if __name__ == "__main__":

    unittest.main()
