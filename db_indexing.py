# Methods whose purpose is to compute additional indexing information for
# magres files

import numpy as np
from soprano.properties.nmr import MSIsotropy


def extractIndexingInfo(magres):
    """Extract all indexing information and return it as a dictionary"""

    iinfo = {}
    iinfo['formula'] = getFormula(magres)
    iinfo['values'] = getMSMetadata(magres)

    return iinfo


def getFormula(magres):
    """Extract chemical formula"""

    symbols = magres.get_chemical_symbols()
    formula = [{'species': s, 'n': symbols.count(s)} for s in set(symbols)]
    formula = sorted(formula, key=lambda x: x['species'])

    return formula


def getMSMetadata(magres):
    """Extract magnetic shieldings"""

    # Chemical species
    symbols = np.array(magres.get_chemical_symbols())
    sp = {s: np.where(symbols == s) for s in set(symbols)}
    isos = MSIsotropy.get(magres)

    msdata = [{'species': s,
               'iso': list(isos[inds])}
              for s, inds in sp.iteritems()]
    msdata = sorted(msdata, key=lambda x: x['species'])

    return msdata
