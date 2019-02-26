# Methods whose purpose is to compute additional indexing information for
# magres files

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import numpy as np
from soprano.properties.nmr import MSIsotropy
from soprano.properties.linkage import Molecules


def _prime_factors(num):

    n = 2
    facs = []
    while num > 1:
        while num % n == 0:
            facs.append(n)
            num = num/n
        n += 1 + (n > 2)  # So past 2 test only odd numbers

    return facs


def extractIndexingInfo(magres):
    """Extract all indexing information and return it as a dictionary"""

    iinfo = {}
    iinfo['formula'] = getFormula(magres)
    iinfo['stochiometry'] = getStochiometry(iinfo['formula'])
    iinfo['values'] = getMSMetadata(magres)

    mols = getMolecules(magres)
    iinfo['Z'] = len(mols)
    iinfo['molecules'] = mols

    return iinfo


def getFormula(magres=None, symbols=None):
    """Extract chemical formula"""

    if symbols is None:
        symbols = magres.get_chemical_symbols()
    else:
        symbols = list(symbols)
    formula = [{'species': s, 'n': symbols.count(s)} for s in set(symbols)]
    formula = sorted(formula, key=lambda x: x['species'])

    return formula


def getStochiometry(formula):
    """Reduce formula to smallest common integer ratios"""

    counts = [_prime_factors(x['n']) for x in formula]

    c = 1
    while all([len(x) > 0 for x in counts]):
        ff = [x.pop(0) for x in counts]
        if len(set(ff)) == 1:
            c *= ff[0]
        else:
            break

    stochio = []
    for x in formula:
        sx = {}
        sx.update(x)
        sx['n'] = int(sx['n']/c)
        stochio.append(sx)

    return stochio


def getMolecules(magres):

    mols = Molecules.get(magres)
    syms = np.array(magres.get_chemical_symbols())

    mols_f = [getFormula(symbols=syms[m.indices]) for m in mols]

    return mols_f


def getMSMetadata(magres):
    """Extract magnetic shieldings"""

    # Chemical species
    symbols = np.array(magres.get_chemical_symbols())
    sp = {s: np.where(symbols == s) for s in set(symbols)}
    isos = MSIsotropy.get(magres)

    msdata = [{'species': s,
               'iso': list(isos[inds])}
              for s, inds in sp.items()]
    msdata = sorted(msdata, key=lambda x: x['species'])

    return msdata
