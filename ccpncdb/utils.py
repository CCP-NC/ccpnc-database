import numpy as np
from io import StringIO
from ase.io.magres import read_magres
from soprano.properties.linkage import Molecules
from soprano.properties.nmr.ms import MSIsotropy


def prime_factors(num):
    # Prime factors of num
    n = 2
    facs = []
    while num > 1:
        while num % n == 0:
            facs.append(n)
            num = num/n
        n += 1 + (n > 2)  # So past 2 test only odd numbers

    return sorted(facs)


def read_magres_file(mfile):
    # Read a magres file/string unifying the output into an ASE Atoms object
    if hasattr(mfile, 'read'):
        mstr = mfile.read()
    else:
        mstr = mfile
    matoms = read_magres(StringIO(str(mstr)))

    return {'string': mstr, 'Atoms': matoms}


def extract_formula(magres=None, symbols=None):
    # Return a list describing the compound's formula
    if symbols is None:
        symbols = magres.get_chemical_symbols()
    else:
        symbols = list(symbols)
    formula = [{'species': s, 'n': symbols.count(s)} for s in set(symbols)]
    formula = sorted(formula, key=lambda x: x['species'])

    return formula


def extract_stochiometry(formula):
    # Stochiometry from formula

    counts = [prime_factors(x['n']) for x in formula]

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


def extract_molecules(magres):

    mols = Molecules.get(magres)
    syms = np.array(magres.get_chemical_symbols())

    mols_f = [extract_formula(symbols=syms[m.indices]) for m in mols]

    return mols_f


def extract_nmrdata(magres):

    # Chemical species
    symbols = np.array(magres.get_chemical_symbols())
    sp = {s: np.where(symbols == s) for s in set(symbols)}
    isos = MSIsotropy.get(magres)

    msdata = [{'species': s,
               'msiso': list(isos[inds])}
              for s, inds in sp.items()]
    msdata = sorted(msdata, key=lambda x: x['species'])

    return msdata
